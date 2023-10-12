from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from api.models.pydantic_models import RequestsCreate, RequestsUpdate, RequestsOutput
from api.models.connection import get_session
from api.models.crud import create_request, get_request_by_id, get_requests, update_request, delete_request
from api.services import provision
from api.services import deploy


router = APIRouter()

### 테스트용 Request CRUD API

@router.get('/test', response_model=list[RequestsOutput], tags=["test"])
def get_test_requests(session: Session = Depends(get_session)):
    requests = get_requests(session)
    return requests

@router.get('/test/{request_id}', response_model=RequestsOutput, tags=["test"])
def get_test_request_by_id(request_id: int, session: Session = Depends(get_session)):
    request = get_request_by_id(session, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    return request

@router.post('/test', response_model=RequestsOutput, tags=["test"])
def create_test_request(request_data: RequestsCreate, session: Session = Depends(get_session)):
    request = create_request(session, request_data)
    return request

@router.put('/test/{request_id}', response_model=RequestsOutput, tags=["test"])
def update_test_request(request_id: int, request_data: RequestsUpdate, session: Session = Depends(get_session)):
    request = get_request_by_id(session, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    request = update_request(session, request, request_data)
    return request

@router.delete('/test/{request_id}', tags=["test"])
def delete_test_request(request_id: int, session: Session = Depends(get_session)):
    request = get_request_by_id(session, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    delete_request(session, request)
    return {"message": "Request deleted successfully"}

# @router.get('/{request_id}/logs')
# async def get_request_logs():
#     return {"Message": "Hello World"}