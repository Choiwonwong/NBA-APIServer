from api.models.connection import CoreV1Api_client, BatchV1Api_client, K8s_client
from kubernetes import utils
from kubernetes.client.rest import ApiException
import yaml

class deployController:
    def __init__(self, namespace):
        self.namespace = namespace
        self.coreV1client = CoreV1Api_client
        self.batchV1client = BatchV1Api_client
    
    def createConfigmap(self, name):
        configmap_name = name
        with open('api/controller/manifest/deploy-config.yaml', 'r') as manifest_file:
            configmap_manifest = yaml.safe_load(manifest_file)
            configmap_manifest['metadata']['name'] = name    
            configmap_manifest['metadata']['namespace'] = self.namespace
            try:
                utils.create_from_dict(K8s_client, configmap_manifest, namespace=self.namespace)
            except ApiException as e:
                raise Exception(f"Failed to create Configmap '{configmap_name}': {e.reason}")
        return f"Configmap '{configmap_name}' created successfully."
    
    def createJob(self, name, configmap_name):
        job_name = name
        with open('api/controller/manifest/deploy.yaml', 'r') as manifest_file:
            job_manifest = yaml.safe_load(manifest_file)
            job_manifest['metadata']['name'] = name    
            job_manifest['metadata']['namespace'] = self.namespace
            job_manifest['spec']['template']['spec']['containers'][0]['envFrom'][0]['configMapRef']['name'] = configmap_name
            try:
                utils.create_from_dict(K8s_client, job_manifest, namespace=self.namespace)
            except ApiException as e:
                raise Exception(f"Failed to create Job '{job_name}': {e.reason}")
        return f"Job '{job_name}' created successfully."