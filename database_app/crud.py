from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from jobjob.database_app import models

# most look up jobs
# highest paid jobs
# same for skills 

def get_job(db: Session, job_id: int):
    return db.query(models.Job).filter(models.Job.job_id == job_id).first()


def get_job_by_link(db: Session, link: str):
    return db.query(models.Job).filter(models.Job.link == link).first()


def get_jobs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Job).offset(skip).limit(limit).all()


def create_job(db: Session, job: models.Job):
    db.add(job)
    db.commit()
    # Refresh if you will use the instance and need any new data from database, like id
    db.refresh(job)
    return job


def get_skills(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Skill).offset(skip).limit(limit).all()


def create_job_skill(db: Session, skill: models.Skill):
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


def get_details(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Detail).offset(skip).limit(limit).all()


def create_job_detail(db: Session, detail: models.Detail):
    db.add(detail)
    db.commit()
    db.refresh(detail)
    return detail


def get_query(db: Session, query: str):
    return db.query(models.Query).filter(models.Query.query == query).first()


def get_queries(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Query).offset(skip).limit(limit).all()


def create_job_rawdata(db: Session, rawdata: models.JobRawData):
    db.add(rawdata)
    db.commit()
    db.refresh(rawdata)
    return rawdata


def create_query(db: Session, query: models.Query):
    db.add(query)
    db.commit()
    db.refresh(query)
    return query


## deprecated as no more query-jobs relationship,
# def create_job_queries(db: Session, query: models.Query):
#     db.add(query)
#     db.commit()
#     db.refresh(query)
#     return query


# # get skills by jobs that are retrieved using queryX (deprecated as we dont crawl by query anymore)
# def get_skills_by_query(db: Session, query: str, limit: int = 10):
#     return (
#         db.query(models.Skill.title)
#         .join(models.Query, models.Query.job_id == models.Skill.job_id)
#         .filter(models.Query.query == query)
#         .group_by(models.Skill.title)
#         .order_by(func.count(models.Skill.title).desc())
#         .limit(limit)
#         .all()
#     )


# get skills from jobs by looking at jobs that contain *query* in title or text
def get_skills_by_query_from_contents(db: Session, query: str, limit: int = 10):
    return (
        db.query(models.Skill.title)
        .join(models.Job, models.Job.id == models.Skill.job_id)
        .filter(
            or_(
                models.Job.text.ilike(f"%{query}%"),
                models.Job.title.ilike(f"%{query}%"),
            )
        )
        .group_by(models.Skill.title)
        .order_by(func.count(models.Skill.title).desc())
        .limit(limit)
        .all()
    )
