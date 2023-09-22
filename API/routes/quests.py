from fastapi import APIRouter

job_router = APIRouter( )

@job_router.post('/', tags=["Job Communication"], summary="Job Communication Endpoint")
async def successBuild():
    return {"messages": "Build Success"}