import pytest
from sqlalchemy.exc import ProgrammingError

from jobjob.database_app import crud, models


# these should call the factories
# move this to a factory file, create jobs in db and also just for handling
def create_jobs(db, n=1):
    return [crud.create_job(db, models.Job(job_id=x, title=f"Test Job {x}", link="link.com")) for x in range(1, n+1)]

def create_skills(db, n=1):
    return [crud.create_job_skill(db, models.Skill(title=f"Test Skill {x}")) for x in range(1, n+1)]

def create_details(db, n=1):
    return [crud.create_job_detail(db, models.Detail(job_type=f"Test Detail job_type {x}")) for x in range(1, n+1)]

def create_queries(db, n=1):
    return [crud.create_query(db, models.Query(query=f"Test Query {x}")) for x in range(1, n+1)]

def test_get_job(db):
    create_jobs(db)
    job = crud.get_job(db, 1)
    assert job.title == "Test Job 1"

def test_get_job_invalid_job_id(db):
    create_jobs(db)
    job = crud.get_job(db, 2)
    assert job is None

def test_get_job_by_link(db):
    create_jobs(db)
    job = crud.get_job_by_link(db, "link.com")
    assert job.link == "link.com"

def test_get_job_by_link_non_existant(db):
    create_jobs(db)
    job = crud.get_job_by_link(db, "linasdfasdfasdfak.com")
    assert job is None

def test_get_jobs_one_job(db):
    created = create_jobs(db)
    jobs = crud.get_jobs(db)
    assert created.pop() in jobs

def test_get_jobs_n_jobs(db):
    n = 5
    created = create_jobs(db, n)
    jobs = crud.get_jobs(db)
    assert all(elem in jobs  for elem in created)
    assert created[n-1].title == f"Test Job {n}"

def test_get_skill(db):
    create_skills(db)
    skills = crud.get_skills(db)
    assert len(skills) == 1
    assert skills[0].title == "Test Skill 1"

def test_get_detail(db):
    n = 3
    create_details(db, n)
    details = crud.get_details(db)
    assert len(details) == n
    assert details[n-1].job_type == f"Test Detail job_type {n}"

def test_get_queries(db):
    n = 3
    create_queries(db, n)
    queries = crud.get_queries(db)
    assert len(queries) == n
    assert queries[n-1].query == f"Test Query {n}"

def test_get_query(db):
    create_queries(db)
    queries = crud.get_query(db, "Test Query 1")
    assert queries.query == f"Test Query 1"

# we are not able to find the existing job? Integrity error - check conftests how session is working
def test_create_raw_data(db):
    jobs = create_jobs(db, 5)
    created_rawdata = crud.create_job_rawdata(db, models.JobRawData(job_id=jobs[0].job_id, raw_data="Test raw data"))
    raw_data = crud.get_raw_data(db)
    assert created_rawdata in raw_data


# sames as previous test
def test_get_skills_by_query(db):
    skill = "Test"
    created_jobs = create_jobs(db, 5)
    crud.create_job_skill(db, models.Skill(title=skill, job_id=created_jobs[0].job_id))
    skills = crud.get_skills_by_query_from_contents(db, skill)
    assert skills
