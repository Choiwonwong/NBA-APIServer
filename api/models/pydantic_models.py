from pydantic import BaseModel
from datetime import datetime

# Request 모델
class RequestsCreate(BaseModel): # 사용자에게 입력을 받는 요소들 딱 이것만 직접 입력 받게됨
    requestTitle: str
    awsAccessKey: str
    awsSecretKey: str

class RequestsUpdate(BaseModel): # 갱신을 위한 검증 폼 - 단계, 프로세스 상태, 프로비전 상태, 배포 상태, 에러 메시지, 시도 횟수 등을 변경할 수 있음
    progress: str | None
    processState: str | None
    provisionState: str | None
    deployState: str | None
    emessage: str | None
    tries: int | None

class RequestsOutput(BaseModel): # 웹서버로 전달을 해주는 모델, 진행 상태에 따라 provisionState 또는 deployState가 None이 될 수 있음
    id: int
    createdAt: datetime
    updatedAt: datetime
    requestTitle: str
    progress: str
    processState: str 
    provisionState: str | None
    deployState: str | None
    emessage: str | None = None
    tries: int

class WebHook(BaseModel):
    request_id: int
    progress: str
    state: str
    emessage: str | None = None
