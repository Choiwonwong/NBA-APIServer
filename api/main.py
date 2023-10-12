from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints import requests, webhook, test

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
        # Check if the connection to the Kubernetes client is working
        if CoreV1Api_client:
            namespaces = CoreV1Api_client.list_namespace()
            namespace_names = [namespace.metadata.name for namespace in namespaces.items]
            return {
                "message": "List of Kubernetes namespaces",
                "namespaces": namespace_names
            }
        else:
            return {
                "error": "Kubernetes client connection not established."
            }
    except Exception as e:
        return {
            "error": f"An error occurred: {str(e)}"
        }
    
@app.get('/pods')
async def get_pods():
    try:
        # Check if the connection to the Kubernetes client is working
        if CoreV1Api_client:
            pods = CoreV1Api_client.list_pod_for_all_namespaces()
            pod_names = [pod.metadata.name for pod in pods.items]
            return {
                "message": "List of Kubernetes pods",
                "pods": pod_names
            }
        else:
            return {
                "error": "Kubernetes client connection not established."
            }
    except Exception as e:
        return {
            "error": f"An error occurred: {str(e)}"
        }

app.include_router(requests.router , prefix='/api/requests')
app.include_router(webhook.router , prefix='/api/webhook')
app.include_router(test.router , prefix='/test-1013')