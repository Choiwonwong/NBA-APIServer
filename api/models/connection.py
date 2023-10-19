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
eks_token = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImNpdmJCc0liaTFHcnhQMmdESFotanpCOEg1ckI0VzhHQnJVZ1dYUlZkZWMifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJhcGkiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlY3JldC5uYW1lIjoibmJhLWFwaS1zYSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VydmljZS1hY2NvdW50Lm5hbWUiOiJuYmEtYXBpLXNhIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQudWlkIjoiZmFmZmU2YzgtNTVlNS00ODdkLWIwYWYtMGFjOWMwMWQzYmZjIiwic3ViIjoic3lzdGVtOnNlcnZpY2VhY2NvdW50OmFwaTpuYmEtYXBpLXNhIn0.irvSQtKioZUx85tsHLP1qg3nclbtoRQgxV3kPegEVFudz6u6J5wEa289iQIZ_mJmXyKQqhJivcsKNe93Nrk--GvHTC0FmbVVuO0ypipoWadPY25XKspe6yXNuGyGPCoDzqsUiF-gB-k0V9Fu6pqR39v7twyb9OBiUYgG84Sr0vQ8RIc3PYOITX2PNLpQZ7jEVwmMjAUBVscbYyQS3ZjFowBCac_iwVI61LwWupD-RCPzVrCXnGW7VWdyffcWrqiBOZeQcrpL_mW_PCf438Qfy0I4Jnor6Xr3W_BufhxZEbv2YCXIylAc_v4i4crJQ5ktXw8WR9VDOZv0J93wHjXZZQ"

configuration = client.Configuration()
configuration.host = eks_url
configuration.verify_ssl = False
# configuration.verify_ssl = True
# configuration.ssl_ca_cert = "/root/.kube/ca.crt"
configuration.debug = True
configuration.api_key = {"authorization": f"Bearer {eks_token}"}

K8s_client = client.ApiClient(configuration)