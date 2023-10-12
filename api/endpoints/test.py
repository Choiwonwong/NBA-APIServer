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
        # 프로세스와 프로비젼 컨트롤러 인스턴스 생성
        process = processController()

        # 네임스페이스 생성
        process.createNamespace(namespace=namespace)

        # AWS 자격 증명 생성
        process.createAwsCredentials(
            namespace, request_body.awsAccessKey, request_body.awsSecretKey
        )
    except Exception as e:
        # 에러가 발생하면 HTTP 예외를 발생시키고 로그를 출력합니다.
        print(e)
        data = {"processState": "실패"}
        update_request(session=session, request= currentRequest, request_data=data)
        raise HTTPException(status_code=500, detail="처리 중 오류 발생")

    # 프로비저닝 진행 중 상태 업데이트
    provision = provisionController(namespace=namespace)

    currentRequest = update_request(
        session=session, request=currentRequest, request_data={"progress": "프로비저닝", "processState": "성공", "provisionState": "시작"}
    )
    try:
        # Pod 생성
        pod_name = "test-full-provision-"+str(id)
        provision.createPod(name=pod_name)

    except Exception as e:
        # 에러가 발생하면 요청 상태를 실패로 업데이트하고 HTTP 예외를 발생시킵니다.
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
        deploy.createJob(name="test-deployment-"+str(id))
    except Exception as e:
        print(e)
        data = {"deployState": "실패"}
        update_request(session=session, request=currentRequest, request_data=data)
        raise HTTPException(status_code=500, detail="처리 중 오류 발생")
    
    update_request(session=session, request=currentRequest, request_data={"deployState": "성공"})
    return {"message": f"{id}에 대한 Job 생성 완료"}


