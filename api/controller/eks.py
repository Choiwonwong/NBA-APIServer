import boto3, eks_token
import os, tempfile, base64
import kubernetes, json

def _write_cafile(data):
    cafile = tempfile.NamedTemporaryFile(delete=False)
    cadata_b64 = data
    cadata = base64.b64decode(cadata_b64)
    cafile.write(cadata)
    cafile.flush()
    return cafile

class UserEKSClientController:
    aws_credentials_path = os.path.expanduser("~/.aws/credentials")
    aws_config_path = os.path.expanduser("~/.aws/config")

    def __init__(self, data):
        self.aws_access_key = data['aws_access_key']
        self.aws_secret_key = data['aws_secret_key']
        self.aws_region = data['aws_region']
        self.cluster_name = data['cluster_name']
        self.dataplane_type = data['dataplane_type']
        self.dataplane_name = data['dataplane_name']
        self.session = boto3.Session( aws_access_key_id=data['aws_access_key'], 
                                     aws_secret_access_key=data['aws_secret_key'], 
                                     region_name=data['aws_region'])
        self.k8sclient = self._get_user_eks_client()
    
    def _create_aws_config(self):
        aws_directory = os.path.expanduser("~/.aws")
        if not os.path.exists(aws_directory):
            os.makedirs(aws_directory)
        with open(self.aws_credentials_path, "w") as credentials_file:
            credentials_file.write(f"[default]\naws_access_key_id = {self.aws_access_key}\naws_secret_access_key = {self.aws_secret_key}")

        with open(self.aws_config_path, "w") as config_file:
            config_file.write(f"[default]\nregion = {self.aws_region}")
    
    def _get_eks_token(self):
        self._create_aws_config()
        token = eks_token.get_token(self.cluster_name)
        os.remove(self.aws_credentials_path)
        os.remove(self.aws_config_path)
        return token
    
    def get_provision_info(self):
        result = {}
        eks_client = self.session.client('eks')
        as_client = self.session.client('autoscaling')

        result["eks_name"] = self.cluster_name
        result["dataplane_name"] = self.dataplane_name
        result["dataplane_type"] = self.dataplane_type

        try:
            eks_infos = eks_client.describe_cluster(name=self.cluster_name)["cluster"]
            result["eks_version"] = eks_infos["version"]
            result["eks_status"] = eks_infos["status"]
            result["eks_endpoint"] = eks_infos["endpoint"]
            result["endpoint"] = eks_infos["endpoint"]
        except KeyError:
            result["eks_version"] = "Not Found"
            result["eks_status"] = "Not Found"
            result["eks_endpoint"] = "Not Found"
            result["endpoint"] = "Not Found"

        if self.dataplane_type == "node-group":
            try:
                ng_infos = eks_client.describe_nodegroup(clusterName=self.cluster_name, nodegroupName=self.dataplane_name)["nodegroup"]
                result["dp_status"] = ng_infos["status"]
                ag_id = ng_infos['resources']['autoScalingGroups'][0]['name']

                try:
                    as_infos = as_client.describe_auto_scaling_groups(AutoScalingGroupNames=[ag_id])['AutoScalingGroups'][0]
                    result["ng_current_count"] = len(as_infos['Instances'])
                except KeyError:
                    result["dp_status"] = "Not Found"
                    result["ng_current_count"] = "Not Found"
            except KeyError:
                result["dp_status"] = "Not Found"
                result["ng_current_count"] = "Not Found"
        else:
            try:
                fg_infos = eks_client.describe_fargate_profile(clusterName=self.cluster_name, fargateProfileName=self.dataplane_name)["fargateProfile"]
                result["dp_status"] = fg_infos["status"]
                result["ng_current_count"] = None
            except KeyError:
                result["dp_status"] = "Not Found"
                result["ng_current_count"] = "Not Found"
        return result
    
    def _get_eks_ca(self):
        eks_client = self.session.client('eks')
        cluster_data = eks_client.describe_cluster(name=self.cluster_name)["cluster"]
        return _write_cafile(cluster_data["certificateAuthority"]["data"])
    
    def _k8s_api_client_config(self, endpoint: str, token: str, cafile: str):
        kconfig = kubernetes.config.kube_config.Configuration(
            host=endpoint,
            api_key={"authorization": f"Bearer {token}"}
        )

        kconfig.ssl_ca_cert = cafile.name
        kconfig.verify_ssl = True 
        kconfig.debug = True
        self.kclient = kubernetes.client.ApiClient(configuration=kconfig)

        return self.kclient
    
    def _get_user_eks_client(self):
        token = self._get_eks_token()['status']['token']
        cafile = self._get_eks_ca()
        client = self.session.client("eks")
        endpoint = client.describe_cluster(name=self.cluster_name)["cluster"]["endpoint"]
        self.eks_client = self._k8s_api_client_config(endpoint, token, cafile)
        return self.eks_client
    
    def get_deploy_info(self, data):
        apps_v1_client = kubernetes.client.AppsV1Api(self.eks_client)
        kube_client = kubernetes.client.CoreV1Api(self.eks_client)
        namespace_name = data['namespace']
        deployment_name = data['deployment_name']
        service_name = data['service_name']
        result = {}
        result["namespace_name"] = namespace_name
        result["deployment_name"] = deployment_name
        result["service_name"] = service_name

        try:
            kube_client.read_namespace(namespace_name)
            result["namespace_status"] = "Found"
        except kubernetes.client.rest.ApiException as e:
            result["namespace_status"] = "Not Found"
        try:
            deployment = apps_v1_client.read_namespaced_deployment(deployment_name, namespace_name)
            result["deployment_status"] = deployment.status.conditions[-1].type
        except kubernetes.client.rest.ApiException as e:
            result["deployment_status"] = "Not Found"

        try:
            pods = kube_client.list_namespaced_pod(namespace_name, label_selector=f'app={deployment_name}')
            if pods is not None and len(pods.items) > 0:
                result["pod_status"] = {}
                for idx in range(len(pods.items)):
                    pod = pods.items[idx]
                    pod_info = {
                        "pod_name": pod.metadata.name,
                        "pod_status": pod.status.phase
                    }    
                    result["pod_status"][str(idx)] = pod_info
            else:
                result["pod_status"] = "Not Found"            
        except:
            result["pods_status"] = "Not Found"

        try:
            service = kube_client.read_namespaced_service(service_name, namespace_name)
        except:
            result["service_type"] = "Not Found"
            result["deployment_port"] = "Not Found"
            result["service_external_ip"] = "Not Found"

        try:
            result["service_type"] = service.spec.type
        except:
            result["service_type"] = "Not Found"

        try:
            result["deployment_port"] = service.spec.ports[0].port
        except:
            result["deployment_port"] = "Not Found"
        try:
            result["service_external_ip"] = service.status.load_balancer.ingress[0].hostname
        except:
            result["service_external_ip"] = "Not Found"
        return json.dumps(result)

# 이 데이터들은 프로비전 정보 제공 + User EKS 접근을 위한 데이터
provision_data = {
    "aws_access_key": "AKIAZBW66YUY3BR4WBUJ",
    "aws_secret_key": "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",
    'aws_region': 'ap-northeast-1',
    'cluster_name': 'nba-eks',
    'dataplane_name': 'eks-node-group',
    'dataplane_type': 'node-group'
}

# 이건 진짜 배포된 것만 보기 위한 데이터가 필요함.
deploy_data = {
    'namespace': 'api',
    'deployment_name': 'nba-api',
    'service_name': 'nba-api-service'
}

# controller = UserEKSClientController(data=provision_data)
# print(controller.get_provision_info())
# print(controller.get_deploy_info(data=deploy_data))