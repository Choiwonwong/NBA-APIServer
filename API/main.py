from fastapi import FastAPI
from .routes import requests, quests

app = FastAPI()
app.include_router(requests.router, prefix='/requests')
app.include_router(quests.build_router, prefix='/build')
app.include_router(quests.provision_router, prefix='/provision')
app.include_router(quests.deploy_router, prefix='/deploy')
