import boto3, eks_token, json
import os, tempfile, base64
import subprocess, kubernetes

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
    
    def check_eks_present(self):
        result = False
        eks_client = self.session.client('eks')
        try:
            eks_client.describe_cluster(name=self.cluster_name)["cluster"]["status"]
            result = True
        except Exception as e:
            print("There is No EKS")
        return result

    def check_ng_present(self):
        result = False
        eks_client = self.session.client('eks')
        try:
            eks_client.describe_nodegroup(clusterName=self.cluster_name, nodegroupName=self.dataplane_name)["nodegroup"]
            result = True
        except Exception as e:
            print("There is No NodeGroup")
        return result
    
    def check_eks_active(self):
        result = False
        eks_client = self.session.client('eks')
        status = eks_client.describe_cluster(name=self.cluster_name)["cluster"]["status"]
        if status == "ACTIVE":
            result = True
        return result
    
    def get_provision_info(self):
        result = {}
        eks_client = self.session.client('eks')
        as_client = self.session.client('autoscaling')
        vpc_client = self.session.client('ec2')

        result["eks_name"] = self.cluster_name
        result["dataplane_name"] = self.dataplane_name
        result["dataplane_type"] = "가상머신"
        result["public_subnet_count"] = 0
        result["private_subnet_count"] = 0
        
        try:
            eks_infos = eks_client.describe_cluster(name=self.cluster_name)["cluster"]
            result["eks_version"] = eks_infos.get("version", not_presented)
            result["eks_status"] = eks_infos.get("status", not_presented)
            result["eks_endpoint"] = eks_infos.get("endpoint", not_presented)
        except Exception as e:
            result["eks_version"] = not_presented
            result["eks_status"] = not_presented
            result["eks_endpoint"] = not_presented        
        
        try:
            vpc_id = eks_client.describe_cluster(name=self.cluster_name)['cluster']['resourcesVpcConfig']['vpcId']
            vpc_response = vpc_client.describe_vpcs(VpcIds=[vpc_id])
            if vpc_response['Vpcs']:
                vpc_tags = vpc_response['Vpcs'][0].get('Tags', [])
                for tag in vpc_tags:
                    if tag['Key'] == 'Name':
                        result["vpc_name"] = tag['Value']        
        except Exception as e:
            result["vpc_name"] = None
        
        try: 
            subnets_ids = eks_client.describe_cluster(name=self.cluster_name)['cluster']['resourcesVpcConfig']['subnetIds']
            subnet_response = vpc_client.describe_subnets(SubnetIds=subnets_ids)['Subnets']
            for subnet in subnet_response:
                is_public = subnet['MapPublicIpOnLaunch']
                if is_public:
                    result["public_subnet_count"] += 1
                else:
                    result["private_subnet_count"] += 1
        except Exception as e:
            pass

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
        result = subprocess.check_output(["python", "api/controller/get_deploy.py", self.aws_access_key, self.aws_secret_key, self.aws_region, self.cluster_name,
                                          data['namespace'], data['deployment_name'], data['service_name'], data['title']])
        return json.loads(result)