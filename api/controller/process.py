from api.models.connection import CoreV1Api_client, BatchV1Api_client
from kubernetes.client.rest import ApiException

class processController:
    def __init__(self):
        self.coreV1client = CoreV1Api_client
        self.batchV1client = BatchV1Api_client

    def create_namespace(self, namespace):
        v1 = self.coreV1client
        body = v1.V1Namespace(metadata=v1.V1ObjectMeta(name=namespace))
        try:
            v1.create_namespace(body)
            print(f"Namespace '{namespace}' created.")
        except ApiException as e:
            print(f"Error creating namespace: {e}")
            self.create_namespace(namespace=namespace + "rescue") 

    def create_aws_credentials(self, namespace, aws_access_key, aws_secret_key):
        v1 = self.coreV1client
        secret = v1.V1Secret(
            metadata=v1.V1ObjectMeta(name="aws-credentials"),
            string_data={
                "AWS_ACCESS_KEY_ID": aws_access_key,
                "AWS_SECRET_ACCESS_KEY": aws_secret_key,
                "AWS_DEFAULT_REGION": "ap-northeast-2",
                "AWS_DEFAULT_OUTPUT": "json"
            }
        )
        try:
            v1.create_namespaced_secret(namespace, secret)
            print("AWS credentials Secret created.")
        except ApiException as e:
            print(f"Error creating AWS credentials Secret: {e}")