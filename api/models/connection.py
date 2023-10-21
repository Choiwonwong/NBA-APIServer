from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from kubernetes import client
import os

# user = os.environ["DB_USER"]
# password = os.environ["DB_PASS"]
# host = os.environ["DB_HOST"]
# port = os.environ["DB_PORT"]
# database = os.environ["DB_NAME"]

# SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://root:test1234@localhost:3306/nba"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_session() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

# eks_url = os.environ.get('EKS_URL')
# eks_token = os.environ.get('token')

eks_url = "https://50FF4DE5E00B95A89855B81B6403F0A6.gr7.ap-northeast-1.eks.amazonaws.com"
eks_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImNpdmJCc0liaTFHcnhQMmdESFotanpCOEg1ckI0VzhHQnJVZ1dYUlZkZWMifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJhcGkiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlY3JldC5uYW1lIjoibmJhLWFwaS1zYSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50Lm5hbWUiOiJuYmEtYXBpLXNhIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQudWlkIjoiNjZlNDA4ZGQtOTVjOS00NmI2LTkzMGYtY2U1MTgzOWE2MmJkIiwic3ViIjoic3lzdGVtOnNlcnZpY2VhY2NvdW50OmFwaTpuYmEtYXBpLXNhIn0.tE2de2AojghsPE0LLfZh3Agaa0wruoccS5pY5fV7obRDFKafVwP3u0-AVhTVruppl3In99wtJiIaqAcInSPUU577aLvt70pt3aBEUp9d_aGkpF9YH2P0RmHyo5yki2WF_JjFrqPgpwTeLBBioU4tbu5NWkK4hHc3dwcOPHjhSX86dd905wINNHp5pTJlNHMfNPFjSo4cwLKuGDOlsDER8c4bQxO-n6VNNXzgXbxH5OX_M7uW6ypZq3wcq2uU00eto7_JI5PntXnQK-BekYOlZMzu8VWlGl5juW27egXGF0xfo__8YASq_7DpYM7IbI3Xe4SK2P79-6u-3gFHsMMdvw"

configuration = client.Configuration()
configuration.host = eks_url
configuration.verify_ssl = False
# configuration.verify_ssl = True
# configuration.ssl_ca_cert = "/root/.kube/ca.crt"
configuration.debug = True
configuration.api_key = {"authorization": f"Bearer {eks_token}"}

K8s_client = client.ApiClient(configuration)