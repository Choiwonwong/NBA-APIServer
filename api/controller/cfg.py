from api.models.connection import K8s_client
from kubernetes import utils, client
from kubernetes.client.rest import ApiException
import yaml

configType = {"provision", "deploy"}
secretType = {"metadata", "awscredentials"}

class ConfigController:
    def __init__(self, namespace):
        self.namespace = namespace
        self.k8sClient = K8s_client

    def createNameSpace(self) -> bool: 
        v1 = self.k8sClient
        namespace = v1.client.V1Namespace(
            metadata=v1.client.V1ObjectMeta(name=self.namespace)
        )
        try:
            v1.create_namespace(namespace)
            return True
        except ApiException as e:
            print(f"Error creating NS: {e}")
            return False

    def createCM(self, type: str, data: dict) -> bool:
        if type not in configType:
            print("Invalid 'type' parameter. It must be 'provision' or 'deployemnt'.")
            return False
            
        name = f"{type}-config"
        with open(f'api/controller/manifest/{type}-config.yaml', 'r') as manifest_file:
            configmap_manifest = yaml.safe_load(manifest_file)
            configmap_manifest['metadata']['name'] = name
            configmap_manifest['metadata']['namespace'] = self.namespace
            for key, value in data.items():
                configmap_manifest['data'][key] = value
            try:
                utils.create_from_dict(K8s_client, configmap_manifest, namespace=self.namespace)
                print(f"ConfigMap '{name}' created in namespace '{self.namespace}'.")
                return True
            except ApiException as e:
                print(f"Error creating ConfigMap: {e}")
                return False
    
    def createSecret(self, name: str, data:dict):
        name = f"{name}-secret"
        v1 = client.CoreV1Api(self.k8sClient)
        secret = {
            'metadata': {
                'name': name
            },
            'stringData': {
                data
            }
        }
        try:
            v1.create_namespaced_secret(self.namespace, secret)
            print("AWS credentials Secret created.")
            return True
        except ApiException as e:
            print(f"Error creating AWS credentials Secret: {e}")
            return False
        
    def getAPIEndPoint(self):
        v1 = client.CoreV1Api(self.k8sClient)
        try:
            api_endpoint = v1.read_namespaced_service("nba-api-service", "api").spec.external_ips[0]
            return api_endpoint
        except ApiException as e:
            print(f"Error getting API endpoint: {e}")
            return False