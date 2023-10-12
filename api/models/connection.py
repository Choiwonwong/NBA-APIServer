from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from kubernetes import client
import os

user = os.environ["DB_USER"]
password = os.environ["DB_PASS"]
host = os.environ["DB_HOST"]
port = os.environ["DB_PORT"]
database = os.environ["DB_NAME"]

SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
# SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://root:test1234@localhost:3306/nba"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_session() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

eks_url = os.environ.get('EKS_URL')
eks_token = os.environ.get('EKS_TOKEN')

configuration = client.Configuration()

configuration.host = eks_url
configuration.verify_ssl = True
configuration.ssl_ca_cert = "/root/.kube/ca.crt"
configuration.debug = True
configuration.api_key = {"authorization": f"Bearer {eks_token}"}

CoreV1Api_client = client.CoreV1Api(client.ApiClient(configuration))
BatchV1Api_client = client.BatchV1Api(client.ApiClient(configuration))