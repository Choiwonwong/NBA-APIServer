from api.models.connection import CoreV1Api_client, BatchV1Api_client, K8s_client
from kubernetes import utils
from kubernetes.client.rest import ApiException
import yaml

class deployController:
    def __init__(self, namespace):
        self.namespace = namespace
        self.coreV1client = CoreV1Api_client
        self.batchV1client = BatchV1Api_client
    
    def createConfigmap(self):
        with open('api/controller/manifest/deploy-config.yaml', 'r') as manifest_file:
            configmap_manifest = yaml.safe_load(manifest_file)   
            configmap_manifest['metadata']['namespace'] = self.namespace
            try:
                utils.create_from_dict(K8s_client, configmap_manifest, namespace=self.namespace)
            except ApiException as e:
                print(f"Failed to create Configmap: {e.reason}")
                raise Exception(f"Failed to create Configmap: {e.reason}")
        print (f"Configmap created successfully.")
        return f"Configmap created successfully."
    
    def createJob(self, name):
        job_name = name
        with open('api/controller/manifest/deploy.yaml', 'r') as manifest_file:
            job_manifest = yaml.safe_load(manifest_file)
            job_manifest['metadata']['name'] = name    
            job_manifest['metadata']['namespace'] = self.namespace
            try:
                utils.create_from_dict(K8s_client, job_manifest, namespace=self.namespace)
            except ApiException as e:
                print(f"Failed to create Job '{job_name}': {e.reason}")
                raise Exception(f"Failed to create Job '{job_name}': {e.reason}")
        return f"Job '{job_name}' created successfully."