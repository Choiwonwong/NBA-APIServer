from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from kubernetes import client
import os

user = os.environ["DB_USER"] # nba
password = os.environ["DB_PASS"] # kakaoschool2023
host = os.environ["DB_HOST"] # nba-rds.cm2oekrnfegh.ap-northeast-1.rds.amazonaws.com
port = os.environ["DB_PORT"] # 2206
database = os.environ["DB_NAME"] # nba

SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"

# SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://root:test1234@localhost:3306/test"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

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