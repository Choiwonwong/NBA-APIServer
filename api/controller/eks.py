import boto3, eks_token
import os, tempfile, base64
import kubernetes

presented = "Found"
not_presented = "Not Found"

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
        self.dataplane_name = data['dataplane_name']
        self.session = boto3.Session( aws_access_key_id=data['aws_access_key'], 
                                     aws_secret_access_key=data['aws_secret_key'], 
                                     region_name=data['aws_region'])
    
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
    
    def _get_eks_ca(self):
        eks_client = self.session.client('eks')
        try:
            cluster_data = eks_client.describe_cluster(name=self.cluster_name)["cluster"]
            return _write_cafile(cluster_data["certificateAuthority"]["data"])
        except Exception as e:
            return False

        
    
    def _k8s_api_client_config(self, endpoint: str, token: str, cafile: str):
        kconfig = kubernetes.config.kube_config.Configuration(
            host=endpoint,
            api_key={"authorization": f"Bearer {token}"}
        )

        kconfig.ssl_ca_cert = cafile.name
        kconfig.verify_ssl = True 
        kconfig.debug = False
        kclient = kubernetes.client.ApiClient(configuration=kconfig)

        return kclient
    
    def _get_user_eks_client(self):
        token = self._get_eks_token()['status']['token']
        cafile = self._get_eks_ca()
        client = self.session.client("eks")
        if cafile is False:
            return False
        try: 
            endpoint = client.describe_cluster(name=self.cluster_name)["cluster"]["endpoint"]
        except Exception as e:
            return False 
        eks_client = self._k8s_api_client_config(endpoint, token, cafile)
        return eks_client
    
    def get_provision_info(self):
        result = {}
        eks_client = self.session.client('eks')
        as_client = self.session.client('autoscaling')

        result["eks_name"] = self.cluster_name
        result["dataplane_name"] = self.dataplane_name
        result["dataplane_type"] = "가상머신"
    
        try:
            eks_infos = eks_client.describe_cluster(name=self.cluster_name)["cluster"]
            result["eks_version"] = eks_infos["version"]
            result["eks_status"] = eks_infos["status"]
            result["eks_endpoint"] = eks_infos["endpoint"]
        except Exception as e:
            result["eks_version"] = not_presented
            result["eks_status"] = not_presented
            result["eks_endpoint"] = not_presented
        try:
            ng_infos = eks_client.describe_nodegroup(clusterName=self.cluster_name, nodegroupName=self.dataplane_name)["nodegroup"]
            result["dp_status"] = ng_infos["status"]
            ag_id = ng_infos['resources']['autoScalingGroups'][0]['name']
            try:
                as_infos = as_client.describe_auto_scaling_groups(AutoScalingGroupNames=[ag_id])['AutoScalingGroups'][0]
                result["ng_current_count"] = len(as_infos['Instances'])
                result["ng_status"] = []
                for instance in as_infos['Instances']:
                    instance_status = {
                    "node_name": instance['InstanceId'],
                    "node_status": instance['LifecycleState']
                    }
                    result["ng_status"].append(instance_status)
            except Exception as e:
                result["dp_status"] = not_presented
                result["ng_current_count"] = not_presented
        except Exception as e:
            result["dp_status"] = not_presented
            result["ng_current_count"] = not_presented
        return result
    
    def get_deploy_info(self, data):
        eks_client= self._get_user_eks_client()
        if eks_client is False:
            return {"eks_present": False}
        
        apps_v1_client = kubernetes.client.AppsV1Api(eks_client)
        kube_client = kubernetes.client.CoreV1Api(eks_client)

        namespace_name = data['namespace']
        deployment_name = data['deployment_name']
        service_name = data['service_name']
        result = {"eks_present": True}
        result["namespace_name"] = namespace_name
        result["deployment_name"] = deployment_name
        result["service_name"] = service_name
      

        try:
            kube_client.read_namespace(namespace_name)
            result["namespace_status"] = presented
        except kubernetes.client.rest.ApiException as e:
            result["namespace_status"] = not_presented
        try:
            deployment = apps_v1_client.read_namespaced_deployment(deployment_name, namespace_name)
            result["deployment_status"] = deployment.status.conditions[-1].type
        except kubernetes.client.rest.ApiException as e:
            result["deployment_status"] = not_presented

        try:
            pods = kube_client.list_namespaced_pod(namespace_name, label_selector=f'app=quest')
            if pods is not None and len(pods.items) > 0:
                result["pod_status"] = []
                for idx in range(len(pods.items)):
                    pod = pods.items[idx]
                    pod_info = {
                        "pod_name": pod.metadata.name,
                        "pod_status": pod.status.phase
                    }    
                    result["pod_status"].append(pod_info) 
            else:
                result["pod_status"] = not_presented            
        except:
            result["pods_status"] = not_presented

        try:
            service = kube_client.read_namespaced_service(service_name, namespace_name)
        except:
            result["service_type"] = not_presented
            result["deployment_port"] = not_presented
            result["service_external_ip"] = not_presented

        try:
            result["service_type"] = service.spec.type
        except:
            result["service_type"] = not_presented

        try:
            result["deployment_port"] = service.spec.ports[0].port
        except:
            result["deployment_port"] = not_presented
        try:
            result["service_external_ip"] = service.status.load_balancer.ingress[0].hostname
        except:
            result["service_external_ip"] = not_presented
        return result