from fastapi import APIRouter

router = APIRouter()

@router.post("/", tags=["requests"], summary="User Request QUEST Service")
async def createRequest():
    return {"messages": "fakecurrentuser"}

@router.get("/", tags=["requests"], summary="Get ALL Request Data")
async def getAllRequests():
    return [{"id": 1}, {"id": 2}]

@router.get("/{id}", tags=["requests"], summary="Get One Request Data")
async def getOneRequest():
    return {"id": id}

