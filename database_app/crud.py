from sqlalchemy.orm import Session
from database_app import models


def get_job(db: Session, job_id: int):
    return db.query(models.Job).filter(models.Job.job_id == job_id).first()


def get_job_by_link(db: Session, link: str):
    return db.query(models.Job).filter(models.Job.link == link).first()


def get_jobs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Job).offset(skip).limit(limit).all()


def create_job(db: Session, job: models.Job):
    db_job = job
    db.add(db_job)
    db.commit()
    # Refresh if you will use the instance and need any new data from database, like id
    db.refresh(db_job)
    return db_job


def get_skills(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Skill).offset(skip).limit(limit).all()


def create_job_skill(db: Session, skill: models.Skill):
    db_skill = skill
    db.add(db_skill)
    db.commit()
    db.refresh(db_skill)
    return db_skill


def get_details(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Detail).offset(skip).limit(limit).all()


def create_job_detail(db: Session, detail: models.Detail):
    db_detail = detail
    db.add(db_detail)
    db.commit()
    db.refresh(db_detail)
    return db_detail
