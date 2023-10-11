from fastapi import APIRouter
from api.services import deploy
from api.services import provision

router = APIRouter()

@router.get('/quests')
async def get_quests():
    return {"Message": "Hello World"}

@router.get('/quests/{quest_id}')
async def get_quest():
    return {"Message": "Hello World"}

@router.post('/quests')
async def create_quest():
    return {"Message": "Hello World"}

@router.get('/quests/{quest_id}/logs')
async def get_quest_logs():
    return {"Message": "Hello World"}
