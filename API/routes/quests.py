from fastapi import APIRouter

build_router = APIRouter( )
provision_router = APIRouter( )
deploy_router = APIRouter( )

@build_router.post('/success', tags=["build"], summary="Build Job Success")
async def successBuild():
    return {"messages": "Build Success"}

@build_router.post('/fail', tags=["build"], summary="Build Job Fail")
async def failBuild():
    return {"messages": "Build Fail"}

@provision_router.post('/success', tags=["provision"], summary="Provision Job Success")
async def successBuild():
    return {"messages": "Provision Success"}

@provision_router.post('/fail', tags=["provision"], summary="Provision Job Fail")
async def failBuild():
    return {"messages": "Provision Fail"}

@deploy_router.post('/success', tags=["deploy"], summary="Deploy Job Success")
async def successBuild():
    return {"messages": "Deploy Success"}

@deploy_router.post('/fail', tags=["deploy"], summary="Deploy Job Fail")
async def failBuild():
    return {"messages": "Deploy Fail"}
