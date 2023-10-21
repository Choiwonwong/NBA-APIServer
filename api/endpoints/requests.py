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

####################### OK
@router.get('/', response_model=list[RequestsOutput], tags=["request"])
def getAllRequests(session: Session = Depends(get_session)):
    requests = get_requests(session)
    return requests


####################### OK
@router.get('/{request_id}', response_model=RequestsOutput, tags=["request"])
def getOneRequest(request_id: int, session: Session = Depends(get_session)):
    request = get_request_by_id(session, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    return request

####################### OK
@router.put('/{request_id}', response_model=RequestsOutput, tags=["request"])
def updateRequest(request_id: int, request_data: RequestsUpdate, session: Session = Depends(get_session)):
    request = get_request_by_id(session, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    request = update_request(session, request, request_data.dict())
    return request

####################### OK
@router.delete('/{request_id}', tags=["request"])
def deleteRequest(request_id: int, session: Session = Depends(get_session)):
    request = get_request_by_id(session, request_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    delete_request(session, request)
    return {"message": "Request deleted successfully"}

####################### OK
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
    

    processController = ProcessController(quest=quest_data, 
                                          access_key= quest_data['AWS인증정보']['AWS계정접근키'],
                                          secret_key=quest_data['AWS인증정보']['AWS계정비밀키'], 
                                          title=quest_data["요청명"],)
    
    resultAWSCR = processController.checkAWSCredential()
    if not resultAWSCR:
        response["message"] = "AWS 인증 정보에 문제가 발생했습니다."
        raise HTTPException(status_code=400, detail=response)

    # # 전처리 - 이자 성공
    processedQuest = processController.processQuestU()
    response["userQuestYaml"] = processedQuest
    response["result"] = "success"
    response["message"] = "모든 검사가 정상적입니다."
    return response


@router.get('/{request_id}/{progress}/logs', tags=["request"])
async def getRequestLogs2(request_id: int, progress: str, session: Session = Depends(get_session)):
    if progress not in ["provision", "deploy"]:
        raise HTTPException(status_code=400, detail="Invalid progress")
    request = get_request_by_id(session, request_id)
    serviceNSName = f"quest-{request.id}"
    ctnController = CTNController(namespace=serviceNSName)
    response = StreamingResponse(ctnController.getLogsStreamer("provision"), media_type="text/event-stream")
    return response

@router.post('/', tags=["request"])
async def createRequest(
    file: UploadFile,
    session: Session = Depends(get_session)
):
    quest_data = None 
    try:
        content = await file.read()
        quest_data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail="YAML 형식 에러입니다. 어떻게 통과하셨죠?")

    request_data = {
        "requestTitle": quest_data['요청_명'],
        "awsAccessKey": quest_data['AWS_인증정보']['AWS_계정_접근_키'],
        "awsSecretKey": quest_data['AWS_인증정보']['AWS_계정_비밀_키'],
    }

    request = create_request(session=session, request_data=request_data)
    # request = get_request_by_id(session, request.id)

    # serviceNSName = f"quest-{request.id}"
    # aws_credentials = {
    #     "AWS_ACCESS_KEY_ID": quest_data['AWS_계정_접근키'],
    #     "AWS_SECRET_ACCESS_KEY": quest_data['AWS_계정_비밀키'],
    #     "AWS_DEFAULT_REGION": quest_data['배포_지역_명'],
    #     "AWS_DEFAULT_OUTPUT": "json"
    # }
    # processController = ProcessController(quest=quest_data, 
    #                                       access_key= aws_credentials["AWS_ACCESS_KEY_ID"],
    #                                       secret_key=aws_credentials["AWS_SECRET_ACCESS_KEY"], 
    #                                       title=quest_data["요청_제목"],)
    # try:
    #     processedQuest = processController.processQuest()
    # except Exception as e:
    #     print(e)
    #     data = {"processState": "실패", "emessage": "An error occurred while processing Quest."}
    #     update_request(session=session, request= request, request_data=data)
    #     raise HTTPException(status_code=500, detail="처리 중 오류 발생")
    
    # configController = ConfigController(namespace=serviceNSName)
    # resultNS = configController.createNameSpace()
    # if not resultNS:
    #     data = {"processState": "실패", "emessage": "Failed to create Namespace."}
    #     update_request(session=session, request= request, request_data=data)
    #     raise HTTPException(status_code=500, detail="Failed to create Namespace.")

    # resultAWSCredentialSecret = configController.createSecret(name="aws-credentials", data=aws_credentials)
    # if not resultAWSCredentialSecret:
    #     data = {"processState": "실패", "emessage": "Failed to create AWS credentials Secret."}
    #     update_request(session=session, request= request, request_data=data)
    #     raise HTTPException(status_code=500, detail="Failed to create AWS credentials Secret.")
    
    # api_endpoint = configController.getAPIEndPoint()
    # metadata = {
    #     "ID": str(request.id),
    #     "API_ENDPOINT": f"{api_endpoint}:8000"
    # }
    # resultMetadataSecret = configController.createSecret(name="meta-data", data=metadata)
    # if not resultMetadataSecret:
    #     data = {"processState": "실패", "emessage": "Failed to create Metadata Secret."}
    #     update_request(session=session, request= request, request_data=data)
    #     raise HTTPException(status_code=500, detail="Failed to create Metadata Secret.")
    
    # resultProvisionCM = configController.createCM(type="provision", data=processedQuest['provision'])
    # if not resultProvisionCM:
    #     data = {"processState": "실패", "emssage": "Failed to create Provision ConfigMap."}
    #     update_request(session=session, request= request, request_data=data)
    #     raise HTTPException(status_code=500, detail="Failed to create Provision ConfigMap.")
    
    # resultDeployCM = configController.createCM(type="deploy", data=processedQuest['deploy'])
    # if not resultDeployCM:
    #     data = {"processState": "실패", "emessage": "Failed to create Deploy ConfigMap."}
    #     update_request(session=session, request= request, request_data=data)
    #     raise HTTPException(status_code=500, detail="Failed to create Deploy ConfigMap.")
    
    # ctnController = CTNController(namespace=serviceNSName)
    # update_request(session=session, request= request, request_data={"processState": "성공", "progress": "프로비저닝", "provisionState": "진행 중"})

    # resultProvisionPod = ctnController.createPod()
    # if not resultProvisionPod:
    #     data = {"provisionState": "실패", "emessage": "Failed to create Provision Pod."}
    #     update_request(session=session, request= request, request_data=data)
    #     raise HTTPException(status_code=500, detail="Failed to create Provision Pod.")
    return request


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
        "dataplane_type": request.dataPlaneType,
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
