from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from api.models.pydantic_models import RequestsUpdate, RequestsOutput
from api.models.connection import get_session
from api.models.crud import create_request, get_request_by_id, get_requests, update_request, delete_request
from api.controller.process import ProcessController, preProcess, get_nested_value, is_english
from api.controller.cfg import ConfigController
from api.controller.ctn import CTNController
from api.controller.eks import UserEKSClientController
import yaml, boto3

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

    if quest_data.get("요청타입", "전체") not in ["전체", "배포"]:
        response["message"] = f"현재는 배포 요청과 전체 요청(프로비저닝 및 배포)만을 지원합니다. 다시 요청해주세요"
        raise HTTPException(status_code=400, detail=response)

    if quest_data.get("AWS인증정보").get("AWS지역명", "도쿄") not in ["서울", "도쿄"]:
        response["message"] = "현재는 서울과 도쿄 지역만 지원합니다. 다시 요청해주세요"
        raise HTTPException(status_code=400, detail=response)

    spec_value = quest_data.get("컴퓨팅요청", {}).get("데이터플레인", {}).get("스펙", "중")
    if spec_value not in ["대", "중"]:
        response["message"] = "가상 머신 스펙은 대(t3.large), 중(t3.medium)만 지원합니다. 다시 요청해주세요"
        raise HTTPException(status_code=400, detail=response)
    
    integer_inputs = [
        ("인터넷_가능_블럭_네트워크", quest_data.get("네트워크환경", {}).get("인터넷가능블럭네트워크", 0)),
        ("인터넷_불가능_블럭_네트워크", quest_data.get("네트워크환경", {}).get("인터넷불가능블럭네트워크", 0)),
        ("가상머신_개수 > 최대", quest_data.get("컴퓨팅요청", {}).get("데이터플레인", {}).get("가상머신개수", {}).get("최대", 0)),
        ("가상머신_개수 > 최소", quest_data.get("컴퓨팅요청", {}).get("데이터플레인", {}).get("가상머신개수", {}).get("최소", 0)),
        ("가상머신_개수 > 요구", quest_data.get("컴퓨팅요청", {}).get("데이터플레인", {}).get("가상머신개수", {}).get("요구", 0)),
        ("컨트롤_플레인 > 버전", quest_data.get("컴퓨팅요청", {}).get("컨트롤플레인", {}).get("버전", 1.0)),
        ("애플리케이션_요청 > 포트_번호", quest_data.get("배포요청", {}).get("애플리케이션", {}).get("포트번호", 0)),
        ("애플리케이션_요청 > 복제본_개수", quest_data.get("배포요청", {}).get("애플리케이션", {}).get("복제본개수", 0)),
    ]
    
    for key, value in integer_inputs:
        try: 
            float(value)
        except:
            response["message"] = f"'{key}'을(를) 정수로 입력해주세요."
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

    if not is_english(quest_data.get("네트워크환경", {}).get("개인작업네트워크이름", "default")):
        response["message"] = "네트워크 이름은 영어(소문자)로 입력해주세요."
        raise HTTPException(status_code=400, detail=response)
    if not is_english(quest_data.get("컴퓨팅요청", {}).get("컨트롤플레인", {}).get("이름", "default")):
        response["message"] = "컨트롤 플레인 이름은 영어(소문자)로 입력해주세요."
        raise HTTPException(status_code=400, detail=response)
    if not is_english(quest_data.get("컴퓨팅요청", {}).get("데이터플레인", {}).get("이름", "default")):
        response["message"] = "데이터 플레인 이름은 영어(소문자)로 입력해주세요."
        raise HTTPException(status_code=400, detail=response)
    if not is_english(quest_data.get("배포요청", {}).get("네임스페이스이름", "default")):
        response["message"] = "네임 스페이스 이름은 영어(소문자)로 입력해주세요."
        raise HTTPException(status_code=400, detail=response)
    if not is_english(quest_data.get("배포요청", {}).get("애플리케이션", {}).get("이름", "default")):
        response["message"] = "앱 이름은 영어(소문자)로 입력해주세요."
        raise HTTPException(status_code=400, detail=response)
    if not is_english(quest_data.get("배포요청", {}).get("서비스", {}).get("이름", "default")):
        response["message"] = "서비스 이름은 영어(소문자)로 입력해주세요."
        raise HTTPException(status_code=400, detail=response)
    
    if quest_data.get("요청타입", "전체") == "배포":
        try:
            quest_data.get("컴퓨팅요청", {}).get("컨트롤플레인", {}).get("이름")
            pass
        except:
            response["message"] = "컨트롤 플레인(EKS) 이름을 입력해주세요."
            raise HTTPException(status_code=400, detail=response)
        try:
            quest_data.get("컴퓨팅요청", {}).get("데이터플레인", {}).get("이름")
            pass
        except:
            response["message"] = "데이터 플레인(노드그룹) 이름을 입력해주세요."
            raise HTTPException(status_code=400, detail=response)

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

    result = {
        "provision" : None,
        "deploy": None,
        "eks_present": False,
        "ng_present": False,
        "eks_active": False,
    }

    userEKSController  = UserEKSClientController(data=controllerData)

    eks_present = userEKSController.check_eks_present()
    ng_present = userEKSController.check_ng_present()

    if eks_present == True:
        provisionData = userEKSController.get_provision_info()
        result["eks_present"] = eks_present
        result["ng_present"] = ng_present
        result["provision"] = provisionData
    else:
        return result    
    eks_active = userEKSController.check_eks_active()

    if eks_active == True:
        deployRequest = {
            'title': request.requestTitle,
            'namespace': request.namespaceName,
            'deployment_name': request.deploymentName,
            'service_name': request.serviceName
        }
        deployData = userEKSController.get_deploy_info(data=deployRequest)
        result["eks_active"] = eks_active
        result["deploy"] = deployData
    
    del userEKSController
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
        "AWS_ACCESS_KEY_ID": request.awsAccessKey,
        "AWS_SECRET_ACCESS_KEY": request.awsSecretKey,
        "AWS_DEFAULT_REGION": request.awsRegionName,
        "AWS_DEFAULT_OUTPUT": "json"
    }
    
    configController = ConfigController(namespace=serviceNSName)
    resultNS = configController.createNameSpace()
    if not resultNS:
        data = {"processState":  "failed", "emessage": "네임 스페이스 생성 실패."}
        update_request(session=session, request= request, request_data=data)
        raise HTTPException(status_code=500, detail="Failed to create Namespace.")

    resultAWSCredentialSecret = configController.createSecret(name="aws-credentials", data=aws_credentials)
    if not resultAWSCredentialSecret:
        data = {"processState":  "failed", "emessage": "AWS 인증 정보 생성 실패"}
        update_request(session=session, request= request, request_data=data)
        raise HTTPException(status_code=500, detail="Failed to create AWS credentials Secret.")
    
    boto_session = boto3.Session(
        aws_access_key_id=request.awsAccessKey, 
        aws_secret_access_key=request.awsSecretKey, 
        region_name=request.awsRegionName
        )

    iam_client = boto_session.client('iam')

    user_id = ":".join(iam_client.get_user()['User']['Arn'].split(":")[:-1])
    
    try:
        iam_client.get_policy(
            PolicyArn=f'{user_id}:policy/AWSLoadBalancerControllerIAMPolicyQUEST'
        )
        PolicyResult= "True"
    except:
        PolicyResult= "False"
    
    try:
        iam_client.get_role(
            RoleName='AmazonEKSLoadBalancerControllerRoleQUEST'
        )
        RoleResult="True"
    except:
        RoleResult="False"
    
    metadata = {
        "ID": str(request.id),
        "API_ENDPOINT": "quest-api-service.quest.svc.cluster.local:8000/api/webhook",
        "LB_POLICY": PolicyResult,
        "LB_ROLE": RoleResult,
    }
    resultMetadataSecret = configController.createSecret(name="meta-data", data=metadata)
    if not resultMetadataSecret:
        data = {"processState":  "failed", "emessage": "메타 데이터 생성 실패."}
        update_request(session=session, request= request, request_data=data)
        raise HTTPException(status_code=500, detail="Failed to create Metadata Secret.")
    
    try:
        processedQuest = processController.processQuestI()
    except Exception as e:
        print(e)
        data = {"processState":  "failed", "emessage": "Quest.yaml 처리 오류"}
        update_request(session=session, request= request, request_data=data)
        raise HTTPException(status_code=500, detail="처리 중 오류 발생")
    
    if quest_data['요청타입'] != "배포":
        resultProvisionCM = configController.createCM(type="provision", data=processedQuest['provision'])
        if not resultProvisionCM:
            data = {"processState":  "failed", "emessage": "프로비저닝 정보 생성 실패"}
            update_request(session=session, request= request, request_data=data)
            raise HTTPException(status_code=500, detail="Failed to create Provision ConfigMap.")
    
    resultDeployCM = configController.createCM(type="deploy", data=processedQuest['deploy'])
    if not resultDeployCM:
        data = {"processState":  "failed", "emessage": "배포 정보 생성 실패"}
        update_request(session=session, request= request, request_data=data)
        raise HTTPException(status_code=500, detail="배포 정보 생성 실패")
    
    ctnController = CTNController(namespace=serviceNSName)
    
    if quest_data['요청타입'] != "배포":
        update_request(session=session, request= request, request_data={"processState":  "success", "progress": "프로비저닝", "provisionState": "start"})
        resultProvisionPod = ctnController.createPod()
        if not resultProvisionPod:
            data = {"provisionState":  "failed", "emessage": "프로비저닝 실행자 생성 실패."}
            update_request(session=session, request= request, request_data=data)
            raise HTTPException(status_code=500, detail="프로비저닝 실행자 생성 실패.")
    else:
        resultProvisionPod = ctnController.createJob()
        update_request(session=session, request= request, request_data={"processState":  "success", "progress": "배포", "provisionState": "skip", "deployState": "start"})
        if not resultProvisionPod:
            data = {"provisionState":  "failed", "emessage": "베포 실행자 생성 실패."}
            update_request(session=session, request= request, request_data=data)
            raise HTTPException(status_code=500, detail="베포 실행자 생성 실패.")
    return request


