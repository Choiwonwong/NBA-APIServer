from api.models.connection import K8s_client
from kubernetes import client
from kubernetes.client.rest import ApiException

configType = {"provision", "deploy"}
secretType = {"metadata", "awscredentials"}

class ConfigController:
    def __init__(self, namespace):
        self.namespace = namespace
        self.k8sClient = K8s_client

    def createNameSpace(self) -> bool: 
        v1 = client.CoreV1Api(self.k8sClient)
        body = {
            'apiVersion': 'v1',
            'kind': 'Namespace',
            'metadata': {
                'name': self.namespace
            }
        }
        try:
            v1.create_namespace(body=body)
            return True
        except ApiException as e:
            print(f"Error creating NS: {e}")
            return False

    def createCM(self, type: str, data: dict) -> bool:
        if type not in configType:
            print("Invalid 'type' parameter. It must be 'provision' or 'deploy'.")
            return False
        
        name = f"{type}-config"
        v1 = client.CoreV1Api(self.k8sClient)
        configmap = {
            'metadata': {
                'name': name
            },
            'data': data
        }
        try:
            v1.create_namespaced_config_map(self.namespace, configmap)
            print(f"{type} ConfigMap created.")
            return True
        except ApiException as e:
            print(f"Error creating AWS credentials Secret: {e}")
            return False
    
    def createSecret(self, name: str, data:dict):
        name = f"{name}"
        v1 = client.CoreV1Api(self.k8sClient)
        secret = {
            'metadata': {
                'name': name
            },
            'stringData': data
        }
        try:
            v1.create_namespaced_secret(self.namespace, secret)
            print("AWS credentials Secret created.")
            return True
        except ApiException as e:
            print(f"Error creating AWS credentials Secret: {e}")
            return False