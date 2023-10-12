from api.models.connection import CoreV1Api_client, BatchV1Api_client
from kubernetes.client.rest import ApiException

class processController:
    def __init__(self):
        self.coreV1client = CoreV1Api_client
        self.batchV1client = BatchV1Api_client

    def createNamespace(self, namespace):
        v1 = self.coreV1client
        body = {
            'metadata': {
                'name': namespace
            }
        }
        try:
            v1.create_namespace(body=body)
            print(f"Namespace '{namespace}' created.")
        except ApiException as e:
            print(f"Error creating namespace: {e}")
            self.createNamespace(namespace=namespace + "-rescue")

    def createAwsCredentials(self, namespace, aws_access_key, aws_secret_key):
        v1 = self.coreV1client
        awsCredentialSecret = {
            'metadata': {
                'name': 'aws-credentials'
            },
            'stringData': {
                'AWS_ACCESS_KEY_ID': aws_access_key,
                'AWS_SECRET_ACCESS_KEY': aws_secret_key,
                'AWS_DEFAULT_REGION': 'ap-northeast-2',
                'AWS_DEFAULT_OUTPUT': 'json'
            }
        }
        try:
            v1.create_namespaced_secret(namespace, awsCredentialSecret)
            print("AWS credentials Secret created.")
        except ApiException as e:
            print(f"Error creating AWS credentials Secret: {e}")