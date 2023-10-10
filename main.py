from fastapi import FastAPI
# from .routes import requests, quests
from connection import Base, engine
from kubernetes import client, config

Base.metadata.create_all(bind=engine)

config.load_kube_config()
api_client = client.CoreV1Api()

app = FastAPI()

@app.get('/')
async def get_namespaces():
    try:
        # Get the list of namespaces
        namespaces = api_client.list_namespace()
        
        # Extract the namespace names
        namespace_names = [namespace.metadata.name for namespace in namespaces.items]
        
        return {
            "message": "List of Kubernetes namespaces",
            "namespaces": namespace_names
        }
    except Exception as e:
        return {
            "error": f"An error occurred: {str(e)}"
        }

# Dependency
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# app.include_router(requests.router, prefix='/api/requests')
# app.include_router(quests.job_router, prefix='/webhook')