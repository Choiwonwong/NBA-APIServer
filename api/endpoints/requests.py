from fastapi import APIRouter
from api.services import deploy
from api.services import provision

router = APIRouter()

@router.get('/')
async def get_all_requests():
    return {"Message": "Hello World"}

@router.get('/{request_id}')
async def get_request():
    return {"Message": "Hello World"}

@router.post('/')
async def create_request():
    return {"Message": "Hello World"}

@router.get('/{request_id}/logs')
async def get_request_logs():
    return {"Message": "Hello World"}
