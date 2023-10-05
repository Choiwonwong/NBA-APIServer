from fastapi import FastAPI
# from .routes import requests, quests
from .connection import Base, engine, SessionLocal


Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# app.include_router(requests.router, prefix='/api/requests')
# app.include_router(quests.job_router, prefix='/webhook')