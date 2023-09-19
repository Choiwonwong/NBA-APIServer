from sqlalchemy.orm import Session

from . import models, schemas


def get_requests(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Request).offset(skip).limit(limit).all()

# def get_request(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(models.Request).offset(skip).limit(limit).all()