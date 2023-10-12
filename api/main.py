from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints import requests, webhook

from api.models.connection import Base, engine, CoreV1Api_client, BatchV1Api_client # services에 포함될 것
import yaml # services에 포함될 것

Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost",  # React 앱의 주소에 맞게 수정
    "http://localhost:3000",  # React 앱의 기본 포트에 맞게 수정
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
async def get_namespaces():
    try:
        namespaces = CoreV1Api_client.list_namespace()
        namespace_names = [namespace.metadata.name for namespace in namespaces.items]
        
        return {
            "message": "List of Kubernetes namespaces",
            "namespaces": namespace_names
        }
    except Exception as e:
        return {
            "error": f"An error occurred: {str(e)}"
        }
    
@app.post('/test')
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

    api_instance = BatchV1Api_client

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

# Dependency
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

app.include_router(requests.router , prefix='/api/requests')
app.include_router(webhook.router , prefix='/api.webhook')