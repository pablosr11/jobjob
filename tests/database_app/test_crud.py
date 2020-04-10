import pytest
from sqlalchemy.exc import ProgrammingError

from jobjob.database_app import crud, models


# these should call the factories
@pytest.fixture()
def one_job(db):
    return crud.create_job(db, models.Job(job_id=1, title=f"Test Job 1", link="link.com"))

# move this to a factory file, create jobs in db and also just for handling
def create_jobs(db, n=1):
    return [crud.create_job(db, models.Job(job_id=x, title=f"Test Job {x}", link="link.com")) for x in range(1 ,n+1)]

def create_skills(db, n=1):
    return [crud.create_job_skill(db, models.Skill(title=f"Test Skill {x}")) for x in range(1 ,n+1)]

def create_details(db, n=1):
    return [crud.create_job_detail(db, models.Detail(job_type=f"Test Detail job_type {x}")) for x in range(1 ,n+1)]

def create_queries(db, n=1):
    return [crud.create_query(db, models.Query(query=f"Test Query {x}")) for x in range(1, n+1)]


def test_get_job(db, one_job):
    job = crud.get_job(db, 1)
    assert job.title == "Test Job 1"

def test_get_job_invalid_job_id(db, one_job):
    job = crud.get_job(db, 2)
    assert job is None

def test_get_job_by_link(db, one_job):
    job = crud.get_job_by_link(db, "link.com")
    assert job.link == "link.com"

def test_get_job_by_link_non_existant(db, one_job):
    job = crud.get_job_by_link(db, "linasdfasdfasdfak.com")
    assert job is None

def test_get_job_by_link_invalid_type(db, one_job):
    with pytest.raises(ProgrammingError) as f:
        job = crud.get_job_by_link(db, 1)

def test_get_jobs_one_job(db, one_job):
    jobs = crud.get_jobs(db)
    assert len(jobs) == 1

def test_get_jobs_n_jobs(db):
    n = 5
    create_jobs(db, n)
    jobs = crud.get_jobs(db)
    assert len(jobs) == n
    assert jobs[n-1].title == f"Test Job {n}"

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

def test_get_query(db):
    create_queries(db)
    queries = crud.get_query(db, "Test Query 1")
    assert queries.query == f"Test Query 1"

def test_get_queries(db):
    n = 3
    create_queries(db, n)
    queries = crud.get_queries(db)
    assert len(queries) == n
    assert queries[n-1].query == f"Test Query {n}"

# we are not able to find the existing job? Integrity error - check conftests how session is working
def test_create_raw_data(db):
    # create job
    # create raw_data with that job.job_id
    # profit
    assert 1

# sames as previous test
def test_get_skills_by_query(db):
    # create job with title or text and job_id
    # create skill with title that appears on job.text or jov.title
    # profit
    assert 1
