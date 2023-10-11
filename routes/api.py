from fastapi import APIRouter
import yaml
from connection import k8s_api_client
router = APIRouter()

@router.post('/')
def createResquest():
    result = create_kubernetes_job()
    return result

def create_kubernetes_job():
    manifest = """
    apiVersion: batch/v1
    kind: Job
    metadata:
      name: pi
    spec:
      template:
        spec:
          containers:
          - name: pi
            image: perl:5.34.0
            command: ["perl", "-Mbignum=bpi", "-wle", "print bpi(2000)"]
          restartPolicy: Never
      backoffLimit: 4
    """
    
    # Parse the YAML manifest into a Python dictionary
    manifest_dict = yaml.safe_load(manifest)

    # Create a Kubernetes API client
    api_instance = k8s_api_client.BatchV1Api()

    # Create the Job resource
    try:
        api_response = api_instance.create_namespaced_job(
            body=manifest_dict,
            namespace="default"  # Specify the namespace in which you want to create the Job
        )
        print("Job created. Status='%s'" % str(api_response.status))
        return {"Message": "Job Created Successfully"}
    except Exception as e:
        print("Error creating Job:", str(e))
        return {"Error": str(e)}