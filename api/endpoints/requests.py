from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from api.models.pydantic_models import RequestsUpdate, RequestsOutput
from api.models.connection import get_session
from api.models.crud import create_request, get_request_by_id, get_requests, update_request, delete_request
from api.controller.process import ProcessController, preProcess, get_nested_value
from api.controller.cfg import ConfigController
from api.controller.ctn import CTNController
from api.controller.eks import UserEKSClientController
import yaml

router = APIRouter()

################################################################################################################### OK
@router.get('/', response_model=list[RequestsOutput], tags=["request"])
def getAllRequests(session: Session = Depends(get_session)):
    requests = get_requests(session)
    return requests


################################################################################################################### OK
@router.get('/{request_id}', response_model=RequestsOutput, tags=["request"])
def getOneRequest(request_id: int, session: Session = Depends(get_session)):
    request = get_request_by_id(session, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    return request

################################################################################################################### OK
@router.put('/{request_id}', response_model=RequestsOutput, tags=["request"])
def updateRequest(request_id: int, request_data: RequestsUpdate, session: Session = Depends(get_session)):
    request = get_request_by_id(session, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    request = update_request(session, request, request_data.dict())
    return request

################################################################################################################### OK
@router.delete('/{request_id}', tags=["request"])
def deleteRequest(request_id: int, session: Session = Depends(get_session)):
    request = get_request_by_id(session, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    delete_request(session, request)
    return {"message": "Request deleted successfully"}

################################################################################################################### OK
@router.post('/check', tags=["request"])
async def checkQuest(file: UploadFile): 
    response = {
        "result": "danger",
        "message": None
    }
    if file.filename == "Quest.yaml":
        try:
            content = await file.read()
            raw_quest_data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            response["message"] = "YAML 형식이 잘못되었습니다."
            raise HTTPException(status_code=400, detail=response)
    else:
        response["message"] = "Quest.yaml을 입력해주세요."
        raise HTTPException(status_code=400, detail=response)
    
    try:
        quest_data = preProcess(raw_quest_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail="YAML 내부 형식이 잘못되었습니다.")
    
    required_fields = [
        "요청명",
        "AWS인증정보.AWS계정접근키",
        "AWS인증정보.AWS계정비밀키",
        "배포요청.애플리케이션.이미지이름",
        "배포요청.애플리케이션.포트번호"
    ]
    
    for field_path in required_fields:
        if not get_nested_value(quest_data, field_path):
            response["message"] = f"'{field_path.replace('.', ' > ')}'가 없습니다."
            raise HTTPException(status_code=400, detail=response)
        
    if quest_data.get("AWS인증정보").get("AWS지역명", None) not in ["서울", "도쿄"]:
        response["message"] = f"현재는 서울과 도쿄 지역만 지원합니다. 다시 요청해주세요"
        raise HTTPException(status_code=400, detail=response)

    spec_value = quest_data.get("컴퓨팅요청", {}).get("데이터플레인", {}).get("스펙", None)
    if spec_value and not spec_value.startswith("t3."):
        response["message"] = f"가상 머신은 현재 t3 계열만 지원합니다. 다시 요청해주세요"
        raise HTTPException(status_code=400, detail=response)
    
    env_list = quest_data.get("배포요청", {}).get("환경변수", None)
    if env_list:
        seen_names = set()  # 중복을 확인하기 위한 이름 집합
        for env_var in env_list:
            name = env_var.get("이름", "")
            if name in seen_names:
                response["message"] = f"환경 변수 이름 '{name}'이 중복되었습니다. 이름은 고유해야 합니다."
                raise HTTPException(status_code=400, detail=response)
            seen_names.add(name)

    processController = ProcessController(quest=quest_data)
    
    resultAWSCR = processController.checkAWSCredential()
    if not resultAWSCR:
        response["message"] = "AWS 인증 정보에 문제가 발생했습니다."
        raise HTTPException(status_code=400, detail=response)

    # 전처리 - 이자 성공
    processedQuest = processController.processQuestU()
    response["userQuestYaml"] = processedQuest
    response["result"] = "success"
    response["message"] = "모든 검사가 정상적입니다."
    return response

################################################################################################################### OK
@router.get('/{request_id}/details/', tags=["request"])
def getOneRequestDetail(request_id: int, session: Session = Depends(get_session)):
    request = get_request_by_id(session, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    controllerData = {
        "aws_access_key": request.awsAccessKey,
        "aws_secret_key": request.awsSecretKey,
        "aws_region": request.awsRegionName,
        "cluster_name": request.clusterName,
        "dataplane_name": request.dataPlaneName
    }

    userEKSController  = UserEKSClientController(data=controllerData)

    deployRequest = {
    'namespace': request.namespaceName,
    'deployment_name': request.deploymentName,
    'service_name': request.serviceName
    }

    provisionData = userEKSController.get_provision_info()
    deployData = userEKSController.get_deploy_info(data=deployRequest)

    result = {
        "provision" : provisionData,
        "deploy": deployData
    }
    return result


################################################################################################################### OK

@router.get('/{request_id}/logs', tags=["request"])
async def getRequestLogs(request_id: int,  session: Session = Depends(get_session)):
    try: 
        request = get_request_by_id(session, request_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="없는 값입니다.")
    serviceNSName = f"quest-{request.id}"
    progress = request.progress
    if progress == "프로비저닝":
        progress = "provision"
    elif progress == "배포":
        progress = "deploy"
    ctnController = CTNController(namespace=serviceNSName)
    response = ctnController.getLogsStreamer(progress=progress)
    logs = StreamingResponse(response, media_type="text/event-stream")
    return logs

@router.post('/', tags=["request"])
async def createRequest(
    file: UploadFile,
    session: Session = Depends(get_session)
):
    raw_quest_data = None 
    try:
        content = await file.read()
        raw_quest_data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail="YAML 형식 에러입니다. 어떻게 통과하셨죠?")
    
    try:
        quest_data = preProcess(raw_quest_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail="YAML 내부 형식이 잘못되었습니다.")
    
    processController = ProcessController(quest=quest_data)

    request_data = processController.processQuestC()
    request = create_request(session=session, request_data=request_data)
    request = get_request_by_id(session, request.id)
    serviceNSName = f"quest-{request.id}"

    aws_credentials = {
        "AWS_ACCESS_KEY_ID": quest_data['AWS계정접근키'],
        "AWS_SECRET_ACCESS_KEY": quest_data['AWS계정비밀키'],
        "AWS_DEFAULT_REGION": quest_data['AWS지역명'],
        "AWS_DEFAULT_OUTPUT": "json"
    }
    
    configController = ConfigController(namespace=serviceNSName)
    resultNS = configController.createNameSpace()
    if not resultNS:
        data = {"processState": "실패", "emessage": "네임 스페이스 생성 실패."}
        update_request(session=session, request= request, request_data=data)
        raise HTTPException(status_code=500, detail="Failed to create Namespace.")

    resultAWSCredentialSecret = configController.createSecret(name="aws-credentials", data=aws_credentials)
    if not resultAWSCredentialSecret:
        data = {"processState": "실패", "emessage": "AWS 인증 정보 생성 실패"}
        update_request(session=session, request= request, request_data=data)
        raise HTTPException(status_code=500, detail="Failed to create AWS credentials Secret.")
    
    api_endpoint = configController.getAPIEndPoint()
    metadata = {
        "ID": str(request.id),
        "API_ENDPOINT": f"{api_endpoint}:8000"
    }
    resultMetadataSecret = configController.createSecret(name="meta-data", data=metadata)
    if not resultMetadataSecret:
        data = {"processState": "실패", "emessage": "메타 데이터 생성 실패."}
        update_request(session=session, request= request, request_data=data)
        raise HTTPException(status_code=500, detail="Failed to create Metadata Secret.")
    
    try:
        processedQuest = processController.processQuestI()
    except Exception as e:
        print(e)
        data = {"processState": "실패", "emessage": "Quest.yaml 처리 오류"}
        update_request(session=session, request= request, request_data=data)
        raise HTTPException(status_code=500, detail="처리 중 오류 발생")
    
    if quest_data['요청_타입'] != "배포":
        resultProvisionCM = configController.createCM(type="provision", data=processedQuest['provision'])
        if not resultProvisionCM:
            data = {"processState": "실패", "emssage": "프로비저닝 정보 생성 실패"}
            update_request(session=session, request= request, request_data=data)
            raise HTTPException(status_code=500, detail="Failed to create Provision ConfigMap.")
    
    resultDeployCM = configController.createCM(type="deploy", data=processedQuest['deploy'])
    if not resultDeployCM:
        data = {"processState": "실패", "emessage": "Failed to create Deploy ConfigMap."}
        update_request(session=session, request= request, request_data=data)
        raise HTTPException(status_code=500, detail="Failed to create Deploy ConfigMap.")
    
    ctnController = CTNController(namespace=serviceNSName)
    
    if quest_data['요청_타입'] != "배포":
        update_request(session=session, request= request, request_data={"processState": "성공", "progress": "프로비저닝", "provisionState": "진행 중"})
        resultProvisionPod = ctnController.createPod()
        if not resultProvisionPod:
            data = {"provisionState": "실패", "emessage": "프로비저닝 실행자 생성 실패."}
            update_request(session=session, request= request, request_data=data)
            raise HTTPException(status_code=500, detail="프로비저닝 실행자 생성 실패.")
    else:
        resultProvisionPod = ctnController.createJob()
        update_request(session=session, request= request, request_data={"processState": "성공", "progress": "배포", "provisionState": "진행 중"})
        if not resultProvisionPod:
            data = {"provisionState": "실패", "emessage": "베포 실행자 생성 실패."}
            update_request(session=session, request= request, request_data=data)
            raise HTTPException(status_code=500, detail="베포 실행자 생성 실패.")
    return request


