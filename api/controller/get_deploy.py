import sys, json
import kubernetes
import boto3, eks_token
import os, tempfile, base64

aws_access_key = sys.argv[1]
aws_secret_key = sys.argv[2]
aws_region = sys.argv[3]
cluster_name = sys.argv[4]
namespace_name = sys.argv[5]
deployment_name = sys.argv[6]
service_name = sys.argv[7]
title = sys.argv[8]

presented = "Found"
not_presented = "Not Found"
aws_credentials_path = os.path.expanduser("~/.aws/credentials")
aws_config_path = os.path.expanduser("~/.aws/config")

session = boto3.Session(
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=aws_region
)

def write_cafile(data):
    cafile = tempfile.NamedTemporaryFile(delete=False)
    cadata_b64 = data
    cadata = base64.b64decode(cadata_b64)
    cafile.write(cadata)
    cafile.flush()
    return cafile

def create_aws_config():
    aws_directory = os.path.expanduser("~/.aws")
    if not os.path.exists(aws_directory):
        os.makedirs(aws_directory)
    with open(aws_credentials_path, "w") as credentials_file:
        credentials_file.write(f"[default]\naws_access_key_id = {aws_access_key}\naws_secret_access_key = {aws_secret_key}")
    with open(aws_config_path, "w") as config_file:
        config_file.write(f"[default]\nregion = {aws_region}")

def get_eks_token():
    create_aws_config()
    token = eks_token.get_token(cluster_name)
    os.remove(aws_credentials_path)
    os.remove(aws_config_path)
    return token

def get_eks_ca():
    eks_client = session.client('eks')
    try:
        cluster_data = eks_client.describe_cluster(name=cluster_name)["cluster"]
        return write_cafile(cluster_data["certificateAuthority"]["data"])
    except Exception as e:
        return False
    
def k8s_api_client_config(endpoint: str, token: str, cafile: str):
    kconfig = kubernetes.config.kube_config.Configuration(
        host=endpoint,
        api_key={"authorization": f"Bearer {token}"}
    )
    kconfig.ssl_ca_cert = cafile.name
    kconfig.verify_ssl = True 
    kconfig.debug = False
    kclient = kubernetes.client.ApiClient(configuration=kconfig)
    return kclient
    
def get_user_eks_client():
    token = get_eks_token()['status']['token']
    cafile = get_eks_ca()
    client = session.client("eks")
    if cafile is False:
        return False
    try: 
        endpoint = client.describe_cluster(name=cluster_name)["cluster"]["endpoint"]
    except Exception as e:
        return False 
    
    eks_client = k8s_api_client_config(endpoint, token, cafile)
    return eks_client

eks_client= get_user_eks_client()
if eks_client is False:
    print (json.dumps({"eks_present": False}))
    sys.exit(0)

apps_v1_client = kubernetes.client.AppsV1Api(eks_client)
kube_client = kubernetes.client.CoreV1Api(eks_client)
result = {}
result["namespace_name"] = namespace_name
result["deployment_name"] = deployment_name
result["service_name"] = service_name
try:
    kube_client.read_namespace(namespace_name)
    result["namespace_status"] = presented
except kubernetes.client.rest.ApiException as e:
    result["namespace_status"] = not_presented
try:
    deployment = apps_v1_client.read_namespaced_deployment(deployment_name, namespace_name)
    result["deployment_status"] = deployment.status.conditions[-1].type
    result["replicas"] = deployment.spec.replicas
    result["image_name"] = deployment.spec.template.spec.containers[0].image
except kubernetes.client.rest.ApiException as e:
    result["deployment_status"] = not_presented
    result["image_name"] = not_presented
    result["replicas"] = not_presented
try:
    pods = kube_client.list_namespaced_pod(namespace_name, label_selector=f'quest={title.lower()}')
    if pods is not None and len(pods.items) > 0:
        result["pod_status"] = []
        for idx in range(len(pods.items)):
            pod = pods.items[idx]
            pod_info = {
                "pod_name": pod.metadata.name,
                "pod_status": pod.status.phase
            }    
            result["pod_status"].append(pod_info) 
    else:
        result["pod_status"] = not_presented
except:
    result["pods_status"] = not_presented
try:
    service = kube_client.read_namespaced_service(service_name, namespace_name)
except:
    result["service_type"] = not_presented
    result["deployment_port"] = not_presented
    result["service_external_ip"] = not_presented
try:
    result["service_type"] = service.spec.type
except:
    result["service_type"] = not_presented
try:
    result["deployment_port"] = service.spec.ports[0].port
except:
    result["deployment_port"] = not_presented
try:
    result["service_external_ip"] = service.status.load_balancer.ingress[0].hostname
except:
    result["service_external_ip"] = not_presented

print(json.dumps(result))