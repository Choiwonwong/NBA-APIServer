from api.models.connection import CoreV1Api_client, BatchV1Api_client, K8s_client
from kubernetes import utils
from kubernetes.client.rest import ApiException
import yaml

class provisionController:
    def __init__(self, namespace):
        self.namespace = namespace
        self.coreV1client = CoreV1Api_client
        self.batchV1client = BatchV1Api_client

    def create_configmap(self, name, data):
        v1 = self.coreV1client
        configmap = v1.client.V1ConfigMap(
            metadata=v1.client.V1ObjectMeta(name=name),
            data=data,
            namespace=self.namespace
        )
        try:
            v1.create_namespaced_config_map(self.namespace, configmap)
            print(f"ConfigMap '{name}' created in namespace '{self.namespace}'.")
        except ApiException as e:
            print(f"Error creating ConfigMap: {e}")

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

