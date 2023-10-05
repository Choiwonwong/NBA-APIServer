from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

user = os.environ["DB_USER"] # nba
password = os.environ["DB_PASS"] # kakaoschool2023
host = os.environ["DB_HOST"] # nba-rds.cm2oekrnfegh.ap-northeast-1.rds.amazonaws.com
port = os.environ["DB_PORT"] # 2206
database = os.environ["DB_NAME"] # nba

SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

