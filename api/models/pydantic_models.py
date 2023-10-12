from pydantic import BaseModel
from datetime import datetime

# Request 모델
class RequestsCreate(BaseModel):
    requestTitle: str
    awsAccessKey: str
    awsSecretKey: str

class RequestsUpdate(BaseModel):
    progress: str
    state: str
    emessage: str

# Provision 모델
class ProvisionCreate(BaseModel):
    state: str
    emessage: str | None = None
    tries: int
    request_id: int

class ProvisionUpdate(BaseModel):
    state: str
    emessage: str | None = None
    tries: int | None

# Deploy 모델
class DeployCreate(BaseModel):
    state: str
    emessage: str | None = None
    tries: int
    request_id: int

class DeployUpdate(BaseModel):
    state: str
    emessage: str | None = None
    tries: int | None

class ProvisionOut(BaseModel):
    id: int
    state: str
    emessage: str | None = None
    tries: int
    request_id: int
    createdAt: datetime
    updatedAt: datetime


class DeployOut(BaseModel):
    id: int
    state: str
    emessage: str | None = None
    tries: int
    request_id: int
    createdAt: datetime
    updatedAt: datetime

class RequestsOutput(BaseModel):
    id: int
    createdAt: datetime
    updatedAt: datetime
    requestTitle: str
    awsAccessKey: str
    awsSecretKey: str
    progress: str
    state: str
    emessage: str | None = None
    provision: ProvisionOut | None = None
    deploy: DeployOut | None = None