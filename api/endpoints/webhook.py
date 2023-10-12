from fastapi import APIRouter
from api.services import deploy
from api.services import provision

router = APIRouter()

@router.post('/')
def webhook():
    return {"Message": "Hello World"}