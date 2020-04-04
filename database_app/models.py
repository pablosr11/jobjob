from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Text, Boolean
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
    text = Column(Text)
    benefits = Column(String)

    raw_data = relationship("JobRawData", backref="jobs", uselist=False)
    skills = relationship("Skill", back_populates="job")
    details = relationship("Detail", back_populates="job")


class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))

    job = relationship("Job", back_populates="skills")


class Detail(Base):
    __tablename__ = "details"

    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String)
    role = Column(String)
    experience_level = Column(String)
    industry = Column(String)
    company_size = Column(String)
    company_type = Column(String)
    job_id = Column(Integer, ForeignKey("jobs.id"))

    job = relationship("Job", back_populates="details")


class Query(Base):
    __tablename__ = "queries"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, index=True)
    location = Column(String)
    salary = Column(String)
    remote = Column(Boolean)


class JobRawData(Base):
    __tablename__ = "raw_data"

    job_id = Column(Integer, ForeignKey("jobs.id"), primary_key=True)
    raw_data = Column(Text)
