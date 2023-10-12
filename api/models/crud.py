from .orm_models import RequestsCreate, RequestsUpdate, RequestsOutput
from .schemas import Request
from sqlalchemy.orm import Session

# To requests Table
# Create a new request
def create_request(session: Session, request_data: RequestsCreate) -> RequestsOutput:
    request = Request(**request_data.dict(), progress="처리 시작", state="진행 중")
    session.add(request)
    session.commit()
    session.refresh(request)
    return RequestsOutput.from_orm(request)

# Get a specific request by ID
def get_request_by_id(session: Session, request_id: int) -> RequestsOutput:
    request = session.get(Request, request_id)
    if not request:
        return None
    return RequestsOutput.from_orm(request)

# Get a list of all requests
def get_requests(session: Session) -> list[RequestsOutput]:
    requests = session.query(Request).all()
    return [RequestsOutput.from_orm(request) for request in requests]

# Update a request
def update_request(session: Session, request: Request, request_data: RequestsUpdate) -> RequestsOutput:
    for field, value in request_data.dict().items():
        setattr(request, field, value)
    session.commit()
    session.refresh(request)
    return RequestsOutput.from_orm(request)

# Delete a request
def delete_request(session: Session, request: Request):
    session.delete(request)
    session.commit()

# # To provisions Table
# def create_provision(session: Session, provision_data: dict):
#     provision = Provision(**provision_data)
#     session.add(provision)
#     session.commit()
#     session.refresh(provision)
#     return provision

# def get_provision_by_id(session: Session, provision_id: int):
#     return session.get(Provision, provision_id)

# def get_provisions(session: Session):
#     return session.query(Provision).all()

# def update_provision(session: Session, provision: Provision, provision_data: dict):
#     for key, value in provision_data.items():
#         setattr(provision, key, value)
#     session.commit()
#     session.refresh(provision)
#     return provision

# def delete_provision(session: Session, provision: Provision):
#     session.delete(provision)
#     session.commit()

# # To deploys Table

# def create_deploy(session: Session, deploy_data: dict):
#     deploy = Deploy(**deploy_data)
#     session.add(deploy)
#     session.commit()
#     session.refresh(deploy)
#     return deploy

# def get_deploy_by_id(session: Session, deploy_id: int):
#     return session.get(Deploy, deploy_id)

# def get_deploys(session: Session):
#     return session.query(Deploy).all()

# def update_deploy(session: Session, deploy: Deploy, deploy_data: dict):
#     for key, value in deploy_data.items():
#         setattr(deploy, key, value)
#     session.commit()
#     session.refresh(deploy)
#     return deploy

# def delete_deploy(session: Session, deploy: Deploy):
#     session.delete(deploy)
#     session.commit()