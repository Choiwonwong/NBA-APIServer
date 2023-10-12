from api.models.connection import CoreV1Api_client, BatchV1Api_client
from kubernetes.client.rest import ApiException
import yaml

class deployController:
    def __init__(self, namespace):
        self.namespace = namespace
        self.coreV1client = CoreV1Api_client()
        self.batchV1client = BatchV1Api_client()
    
    def createJob(self, name):
    # Define the name of the Job resource.
        job_name = name

        # Read the contents of the YAML manifest file.
        manifest_filename = 'controller/manifest/deploy.yaml'
        manifest = self.read_yaml_manifest(manifest_filename)

        # Create a V1Job object with the manifest data.
        job = self.batchV1client.V1Job(
            metadata=self.batchV1client.V1ObjectMeta(name=job_name, namespace=self.namespace),
            spec=manifest['spec']  # Assuming the manifest contains a 'spec' section.
        )

        try:
            # Create the Job resource.
            self.batchV1client.create_namespaced_job(self.namespace, job)

            # You can add additional logic here for error handling or logging.

            return f"Job '{job_name}' created successfully."
        except ApiException as e:
            # Handle the exception (e.g., log the error or raise a custom exception).
            raise Exception(f"Failed to create Job '{job_name}': {e.reason}")