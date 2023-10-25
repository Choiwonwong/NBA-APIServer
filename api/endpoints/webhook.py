from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from api.models.pydantic_models import WebHook
from api.models.connection import get_session
from api.models.crud import get_request_by_id, update_request
from api.controller.ctn import CTNController

router = APIRouter()

@router.post('/webhook', tags=['webhook'])
def webhook(webhookData: WebHook, session: Session = Depends(get_session)):
    request = get_request_by_id(session, webhookData.id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    
    progress = webhookData.progress
    state = webhookData.state
    emessage = webhookData.emessage

    ctnController = CTNController(namespace=f"quest-{request.id}")

    if progress == "provision" and state == "success":
        # 배포 잡 생성
        update_request(session, request, {"progress": "deploy", "provisionState": "성공", "deployState": "시작"})
        resultDeployJob = ctnController.createJob()
        if not resultDeployJob:
            data = {"provisionState": "실패", "emessage": "Failed to create Provision Pod."}
            update_request(session=session, request= request, request_data=data)
            raise HTTPException(status_code=500, detail="Failed to create Provision Pod.")
        
    elif progress == "provision" and state == "failed":
        update_request(session, request, {"progress": "deploy", "provisionState": "실패", "emessage": emessage})
        resultProvisionPod = ctnController.createPod()
        if not resultProvisionPod:
            data = {"provisionState": "실패", "emesage": "Failed to create Provision Pod."}
            update_request(session=session, request= request, request_data=data)
            raise HTTPException(status_code=500, detail="Failed to create Provision Pod.")

    elif progress == "deploy" and state == "success":
        update_request(session, request, {"progress": "deploy", "deployState": "성공"})
    
    elif progress == "deploy" and state == "failed":
        update_request(session, request, {"progress": "deploy", "deployState": "실패", "emessage": emessage})
        resultDeployJob = ctnController.createJob()
        if not resultDeployJob:
            data = {"deployState": "실패", "emessage": "Failed to create Deploy Job."}
            update_request(session=session, request= request, request_data=data)
            raise HTTPException(status_code=500, detail="Failed to create Deploy Job.")
    return {"message": f"{progress}단계 {state} 처리 완료"}