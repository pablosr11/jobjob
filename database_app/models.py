from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Text, PickleType
from sqlalchemy.orm import relationship

from database_app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, index=True)
    title = Column(String)
    link = Column(String, index=True)
    company = Column(String, nullable=True)
    city = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    min_salary = Column(Integer, index=True, nullable=True)
    max_salary = Column(Integer, index=True, nullable=True)
    date_posted = Column(DateTime, nullable=True)

    # skills = relationship("Skill", back_populates="job")

    text = Column(Text)
    benefits = Column(String)
    # details = Column(String) # Multiple Key values
    # raw_data = Column(PickleType) # Lxml Element instance


# class Skill(Base):
#     __tablename__ = "skills"
#     id = Column(Integer, primary_key=True, index=True)
#     title = Column(String, index=True)
#     job_id = Column(Integer, ForeignKey("jobs.id"))

#     job = relationship("Job", back_populates="skills")


# need relationships tables between job-query and job-skill

###### Not in v1
# class Query(Base):
#     __tablename__ = "queries"


# class Detail(Base):
#     ...
