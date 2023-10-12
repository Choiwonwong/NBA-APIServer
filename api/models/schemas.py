from datetime import datetime, timedelta
from sqlalchemy.sql import func
from sqlmodel import SQLModel, Field, Relationship

class Request(SQLModel, table=True):
    __tablename__ = "requests"
    id: int = Field(primary_key=True)
    createdAt: datetime = Field(default=func.now() + timedelta(hours=9))
    updatedAt: datetime = Field(default=func.now() + timedelta(hours=9))
    requestTitle: str
    awsAccessKey: str
    awsSecretKey: str
    progress: str
    state: str
    emessage: str = None
    provision: "Provision" = Relationship(back_populates="request")
    deploy: "Deploy" = Relationship(back_populates="request")

class Provision(SQLModel, table=True):
    __tablename__ = "provisions"
    id: int = Field(primary_key=True)
    state: str
    emessage: str = None
    createdAt: datetime = Field(default=func.now() + timedelta(hours=9))
    updatedAt: datetime = Field(default=func.now() + timedelta(hours=9))
    tries: int
    request_id: int = Field(index=True, foreign_key="requests.id")
    request: "Request" = Relationship(back_populates="provision")

class Deploy(SQLModel, table=True):
    __tablename__ = "deploys"
    id: int = Field(primary_key=True)
    state: str
    emessage: str = None
    createdAt: datetime = Field(default=func.now() + timedelta(hours=9))
    updatedAt: datetime = Field(default=func.now() + timedelta(hours=9))
    tries: int
    request_id: int = Field(index=True, foreign_key="requests.id")
    request: "Request" = Relationship(back_populates="deploy")