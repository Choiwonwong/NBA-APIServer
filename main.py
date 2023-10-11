from fastapi import FastAPI
from routes import api
from routes import webhook
from connection import Base, engine, CoreV1Api_client

Base.metadata.create_all(bind=engine)

# eks_url = os.environ.get('EKS_URL')
# eks_token = os.environ.get('EKS_TOKEN')

# configuration = client.Configuration()

# configuration.host = eks_url
# configuration.verify_ssl = False
# configuration.debug = True
# configuration.api_key = {"authorization": f"Bearer {eks_token}"}
# api_client = client.CoreV1Api(client.ApiClient(configuration))

app = FastAPI()

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

# Dependency
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

app.include_router(api.router, prefix='/api')
app.include_router(webhook.router, prefix='/webhook')