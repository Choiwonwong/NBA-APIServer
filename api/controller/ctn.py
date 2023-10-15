from api.models.connection import K8s_client
from kubernetes import utils, client
from kubernetes.client.rest import ApiException
import yaml
import asyncio

class CTNController:
    def __init__(self, namespace):
        self.namespace = namespace
        self.k8sClient = K8s_client

    def createPod(self) -> bool:
        with open('api/controller/manifest/provision.yaml', 'r') as manifest_file:
            pod_manifest = yaml.safe_load(manifest_file)
            try:
                utils.create_from_dict(self.k8sClient, pod_manifest, namespace=self.namespace)
                print(f"Pod created in namespace '{self.namespace}'.")
                return True
            except ApiException as e:
                print(f"Error creating Pod: {e}")
                return False
            
    def createJob(self) -> bool:
        with open('api/controller/manifest/deploy.yaml', 'r') as manifest_file:
            job_manifest = yaml.safe_load(manifest_file)
            try:
                utils.create_from_dict(self.k8sClient, job_manifest, namespace=self.namespace)
                return True
            except ApiException as e:
                print(f"Failed to create Job: {e.reason}")
                return False

    def getLogs(self, progress):
        if progress == "provision":
            pod_name = "provision"
        elif progress == "deploy":
            pod_name = "job.batch/deploy"
        else:
            raise Exception("Invalid progress")
        v1 = client.CoreV1Api(self.k8sClient)
        try:
            return v1.read_namespaced_pod_log(pod_name, self.namespace)
        except ApiException as e:
            print(f"Failed to get logs: {e.reason}")
            return False
        
    async def getLogsStreamer(self, progress):
        if progress == "provision":
            pod_name = "provision"
        elif progress == "deploy":
            pod_name = "job.batch/deploy"
        else:
            raise Exception("Invalid progress")
        v1 = client.CoreV1Api(self.k8sClient)
        try:
            response = v1.read_namespaced_pod_log(name=pod_name, namespace=self.namespace, follow=True, _preload_content=False)
            for log in response:
                yield f"data: {log}\n\n"
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            print("caught canceled error")