from fastapi import FastAPI
from .routes import requests, quests

app = FastAPI()
app.include_router(requests.router, prefix='/api/requests')
app.include_router(quests.job_router, prefix='/webhook')