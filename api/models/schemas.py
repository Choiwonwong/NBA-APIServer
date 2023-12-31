from datetime import datetime
# from sqlalchemy.sql import func
from sqlmodel import SQLModel, Field

class Request(SQLModel, table=True):
    __tablename__ = "requests"
    id: int = Field(primary_key=True)
    createdAt: datetime 
    updatedAt: datetime
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
    clusterName: str
    dataPlaneName: str
    namespaceName: str
    deploymentName: str
    serviceName: str