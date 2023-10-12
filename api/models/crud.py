from models.models import Request, Provision, Deploy
from sqlmodel import Session

# To requests Table
def create_request(session: Session, request_data: dict):
    request = Request(**request_data)
    session.add(request)
    session.commit()
    session.refresh(request)
    return request

def get_request_by_id(session: Session, request_id: int):
    return session.get(Request, request_id)

def get_requests(session: Session):
    return session.query(Request).all()

def update_request(session: Session, request: Request, request_data: dict):
    for key, value in request_data.items():
        setattr(request, key, value)
    session.commit()
    session.refresh(request)
    return request

def delete_request(session: Session, request: Request):
    session.delete(request)
    session.commit()

# To provisions Table
def create_provision(session: Session, provision_data: dict):
    provision = Provision(**provision_data)
    session.add(provision)
    session.commit()
    session.refresh(provision)
    return provision

def get_provision_by_id(session: Session, provision_id: int):
    return session.get(Provision, provision_id)

def get_provisions(session: Session):
    return session.query(Provision).all()

def update_provision(session: Session, provision: Provision, provision_data: dict):
    for key, value in provision_data.items():
        setattr(provision, key, value)
    session.commit()
    session.refresh(provision)
    return provision

def delete_provision(session: Session, provision: Provision):
    session.delete(provision)
    session.commit()

# To deploys Table

def create_deploy(session: Session, deploy_data: dict):
    deploy = Deploy(**deploy_data)
    session.add(deploy)
    session.commit()
    session.refresh(deploy)
    return deploy

def get_deploy_by_id(session: Session, deploy_id: int):
    return session.get(Deploy, deploy_id)

def get_deploys(session: Session):
    return session.query(Deploy).all()

def update_deploy(session: Session, deploy: Deploy, deploy_data: dict):
    for key, value in deploy_data.items():
        setattr(deploy, key, value)
    session.commit()
    session.refresh(deploy)
    return deploy

def delete_deploy(session: Session, deploy: Deploy):
    session.delete(deploy)
    session.commit()