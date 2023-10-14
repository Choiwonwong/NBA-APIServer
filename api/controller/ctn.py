from api.models.connection import K8s_client
from kubernetes import utils
from kubernetes.client.rest import ApiException
import yaml

class CTNController:
    def __init__(self, namespace):
        self.namespace = namespace
        self.k8sClient = K8s_client

    def createPod(self, name):
        with open('api/controller/manifest/provision.yaml', 'r') as manifest_file:
            pod_manifest = yaml.safe_load(manifest_file)

            pod_manifest['metadata']['name'] = name    
            pod_manifest['metadata']['namespace'] = self.namespace

            try:
                utils.create_from_dict(K8s_client, pod_manifest, namespace=self.namespace)
                print(f"Pod '{name}' created in namespace '{self.namespace}'.")
            except ApiException as e:
                print(f"Error creating Pod: {e}")

                

# def createJob(self, name):
    #     job_name = name
    #     with open('api/controller/manifest/deploy.yaml', 'r') as manifest_file:
    #         job_manifest = yaml.safe_load(manifest_file)
    #         job_manifest['metadata']['name'] = name    
    #         job_manifest['metadata']['namespace'] = self.namespace
    #         try:
    #             utils.create_from_dict(K8s_client, job_manifest, namespace=self.namespace)
    #         except ApiException as e:
    #             print(f"Failed to create Job '{job_name}': {e.reason}")
    #             raise Exception(f"Failed to create Job '{job_name}': {e.reason}")
    #     return f"Job '{job_name}' created successfully."