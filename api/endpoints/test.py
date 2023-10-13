from fastapi import APIRouter, HTTPException, Depends
from api.controller.process import processController
from api.controller.provision import provisionController
from api.controller.deploy import deployController
from api.models.pydantic_models import RequestsCreate
from api.models.crud import create_request, update_request, get_request_by_id
from api.models.connection import get_session
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/fullprovisiontest/{id}", tags=["[1013]test"])
async def full_provision_test(id: int, request_body: RequestsCreate, session: Session = Depends(get_session)):
    currentRequest =create_request (session=session, request_data=request_body)
    namespace = "test-" + str(id)
    try:
        process = processController()
        process.createNamespace(namespace=namespace)
        process.createAwsCredentials(
            namespace, request_body.awsAccessKey, request_body.awsSecretKey
        )
    except Exception as e:
        print(e)
        data = {"processState": "실패"}
        update_request(session=session, request= currentRequest, request_data=data)
        raise HTTPException(status_code=500, detail="처리 중 오류 발생")

    provision = provisionController(namespace=namespace)

    currentRequest = update_request(
        session=session, request=currentRequest, request_data={"progress": "프로비저닝", "processState": "성공", "provisionState": "시작"}
    )
    try:
        pod_name = "test-full-provision-"+str(id)
        provision.createPod(name=pod_name)

    except Exception as e:
        update_request(session=session, request=currentRequest, request_data={"progress": "프로비저닝", "provisionState": "실패"})
        print(e)
        raise HTTPException(status_code=500, detail="Pod 생성 중 오류 발생")

    # 프로비저닝 완료 상태 업데이트
    update_request(
        session=session, request=currentRequest,request_data={"progress": "프로비저닝", "provisionState": "성공"}
    )
    return {"message": f"{id}에 대한 Full Provisioning Pod 생성 완료"}

@router.post("/deploytest/{id}", tags=["[1013]test"])
def deploy_test(id: int, session: Session = Depends(get_session)):
    currentRequest = get_request_by_id(session=session, request_id=id)
    namespace = "test-" + str(id)
    currentRequest = update_request(session=session, request=currentRequest, request_data={"progress": "배포", "deployState": "시작"})
    try:
        deploy = deployController(namespace=namespace)
        deploy.createConfigmap()
        deploy.createJob(name="test-deployment-"+str(id))
    except Exception as e:
        print(e)
        data = {"deployState": "실패"}
        update_request(session=session, request=currentRequest, request_data=data)
        raise HTTPException(status_code=500, detail="처리 중 오류 발생")
    
    update_request(session=session, request=currentRequest, request_data={"deployState": "성공"})
    return {"message": f"{id}에 대한 Job 생성 완료"}


