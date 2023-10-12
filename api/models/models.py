from pydantic import BaseModel
from datetime import date

# Pydantic 모델 (입력 유효성 검사)
class RequestsCreate(BaseModel):
    requestTitle: str
    awsAccessKey: str
    awsSecretKey: str

# Pydantic 모델 (업데이트 유효성 검사)
class RequestsUpdate(BaseModel):
    progress: str
    state: str
    emessage: str

# Pydantic 모델 (출력 형식)
class RequestsOutput(BaseModel):
    id: int
    createdAt: date
    updatedAt: date
    requestTitle: str
    awsAccessKey: str
    awsSecretKey: str
    progress: str
    state: str
    emessage: str

