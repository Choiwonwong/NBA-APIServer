from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints import requests, webhook
from api.models.connection import K8s_client
from kubernetes import client
import logging, time

class EndpointFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return record.getMessage().find("/api/health") == -1
    
log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
logging.basicConfig(filename='http_requests.log', level=logging.INFO, format=log_format)

app = FastAPI(docs_url='/api/docs', openapi_url='/api/openapi.json')

origins = [
    "https://www.quest-nba.com",
    "https://www.quest-nba.com/",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(requests.router , prefix='/api/requests')
app.include_router(webhook.router , prefix='/api')

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # HTTP 요청 정보를 로그에 기록
    log_message = f"{request.client} - {request.method} {request.url} - {response.status_code}"
    logging.info(log_message)
    
    return response

@app.get('/api/health', tags=['healthcheck'])
async def get_namespaces():
    CoreV1Api_client = client.CoreV1Api(K8s_client)
    try:
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
    
logging.getLogger("uvicorn.access").addFilter(EndpointFilter())
