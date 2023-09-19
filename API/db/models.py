from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, Float
from sqlalchemy.orm import relationship

from connection import Base

class Request(Base):
    __tablename__ = "requestT"
    id = Column(Integer, primary_key=True, index=True)
    Repo = Column(String)
    Branch = Column(String)
    AK = Column(String)
    SK = Column(String)
    createdAt = Column(Date)
    updatedAt = Column(Date)