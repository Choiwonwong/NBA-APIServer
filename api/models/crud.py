from .schemas import Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

def create_request(session: Session, request_data: dict) -> Request:
    request_dict = request_data
    new_request = Request(
        **request_dict,
        progress="처리",
        processState="start",
        createdAt=datetime.now() + timedelta(hours=9),
        updatedAt=datetime.now() + timedelta(hours=9),
    )
    session.add(new_request)
    session.commit()
    session.refresh(new_request)
    return new_request

# Get a specific request by ID
def get_request_by_id(session: Session, request_id: int) -> Request:
    request = session.get(Request, request_id)
    if not request:
        return None
    return request

# Get a list of all requests
def get_requests(session: Session) -> list[Request]:
    requests = session.query(Request).all()
    return requests

# Update a request
def update_request(session: Session, request: Request, request_data: dict) -> Request:
    for field, value in request_data.items() :
        setattr(request, field, value)
    setattr(request, "updatedAt", datetime.now() + timedelta(hours=9))
    session.commit()
    session.refresh(request)
    return request

# Delete a request
def delete_request(session: Session, request: Request):
    session.delete(request)
    session.commit()