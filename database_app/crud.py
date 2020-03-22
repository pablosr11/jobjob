from sqlalchemy.orm import Session
from database_app import models


def get_job(db: Session, job_id: int):
    return db.query(models.Job).filter(models.Job.job_id == job_id).first()


def get_job_by_link(db: Session, link: str):
    return db.query(models.Job).filter(models.Job.link == link).first()


def get_jobs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Job).offset(skip).limit(limit).all()


def create_job(db: Session, job: models.Job):
    db_job = models.Job(
        job_id=job.job_id,
        title=job.title,
        link=job.link,
        company=job.company,
        city=job.city,
        postal_code=job.postal_code,
        min_salary=job.min_salary,
        max_salary=job.max_salary,
        date_posted=job.date_posted,
        text=job.text,
        benefits = job.benefits,
        # raw_data = job.raw_data,
    )
    db.add(db_job)
    db.commit()
    # Refresh if you will use the instance and need any new data from database, like id
    db.refresh(db_job)
    return db_job


# def get_skills(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(models.Skill).offset(skip).limit(limit).all()

# def create_job_skill(db:Session, skill:models.Skill, job_id:int):
#     db_skill = models.Skill(job_id=job_id)
#     db.add(db_skill)
#     db.commit()
#     db.refresh(db_skill)
#     return db_skill
