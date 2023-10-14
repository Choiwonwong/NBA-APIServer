from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints import requests, webhook

from api.models.connection import K8s_client
from kubernetes import client

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

app.include_router(requests.router , prefix='/api/requests')
app.include_router(webhook.router , prefix='/api/webhook', deprecated=True)

@app.get('/')
async def get_namespaces():
    CoreV1Api_client = client.CoreV1Api(K8s_client)
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