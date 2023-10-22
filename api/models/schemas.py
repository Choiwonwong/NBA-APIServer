from datetime import datetime, timedelta
from sqlalchemy.sql import func
from sqlmodel import SQLModel, Field

class Request(SQLModel, table=True):
    __tablename__ = "requests"
    id: int = Field(primary_key=True)
    createdAt: datetime = Field(default=func.now() + timedelta(hours=9))
    updatedAt: datetime = Field(default=func.now() + timedelta(hours=9))
    requestTitle: str
    requestType: str
    awsAccessKey: str
    awsSecretKey: str
    awsRegionName: str
    progress: str
    processState: str | None = None
    provisionState: str | None = None
    deployState: str | None = None
    emessage: str | None = None
    tries: int = 0
    clusterName: str
    dataPlaneType: str
    dataPlaneName: str
    namespaceName: str
    deploymentName: str
    serviceName: str