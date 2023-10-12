from fastapi import APIRouter
from api.controller.process import processController
from api.controller.provision import provisionController
from api.controller.deploy import deployController

router = APIRouter()

@router.post('/')
def webhook():
    return {"Message": "Hello World"}