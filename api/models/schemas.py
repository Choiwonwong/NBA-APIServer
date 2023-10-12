from sqlmodel import SQLModel, Field, Relationship
from datetime import date
import sqlalchemy as sa

# SQLModel 모델
class Request(SQLModel, table=True):
    __tablename__ = "requests"
    uuid: bytes = Field(default=None, primary_key=True, index=True)
    id: int = Field(sa_column=sa.Column(autoincrement=True))
    createdAt: date = Field(default=None)
    updatedAt: date = Field(default=None)
    requestTitle: str
    awsAccessKey: str
    awsSecretKey: str
    progress: str
    state: str
    emessage: str = Field(default=None)
    provisions: list['Provision'] = Relationship(back_populates="request")
    deploys: list['Deploy'] = Relationship(back_populates="request")

class Provision(SQLModel, table=True):
    __tablename__ = "provisions"
    provision_uuid: bytes = Field(default=None, primary_key=True, index=True)
    id: int = Field(sa_column=sa.Column(autoincrement=True))
    state: str
    emessage: str = Field(default=None)
    createdAt: date = Field(default=None)
    updatedAt: date = Field(default=None)
    tries: int
    request_uuid: bytes = Field(index=True, foreign_key="requests.uuid")
    request: Request = Relationship(back_populates="provisions")

class Deploy(SQLModel, table=True):
    __tablename__ = "deploys"
    deploy_uuid: bytes = Field(default=None, primary_key=True, index=True)
    id: int = Field(sa_column=sa.Column(autoincrement=True))
    state: str
    emessage: str = Field(default=None)
    createdAt: date = Field(default=None)
    updatedAt: date = Field(default=None)
    tries: int
    request_uuid: bytes = Field(index=True, foreign_key="requests.uuid")
    request: Request = Relationship(back_populates="deploys")