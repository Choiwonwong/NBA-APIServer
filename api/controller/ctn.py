from api.models.connection import K8s_client
from kubernetes import utils
from kubernetes.client.rest import ApiException
import yaml

class CTNController:
    def __init__(self, namespace):
        self.namespace = namespace
        self.k8sClient = K8s_client

    def createPod(self) -> bool:
        with open('api/controller/manifest/provision.yaml', 'r') as manifest_file:
            pod_manifest = yaml.safe_load(manifest_file)
            try:
                utils.create_from_dict(self.K8s_client, pod_manifest, namespace=self.namespace)
                print(f"Pod created in namespace '{self.namespace}'.")
                return True
            except ApiException as e:
                print(f"Error creating Pod: {e}")
                return False
            
    def createJob(self) -> bool:
        with open('api/controller/manifest/deploy.yaml', 'r') as manifest_file:
            job_manifest = yaml.safe_load(manifest_file)
            try:
                utils.create_from_dict(self.K8s_client, job_manifest, namespace=self.namespace)
                return True
            except ApiException as e:
                print(f"Failed to create Job: {e.reason}")
                return False