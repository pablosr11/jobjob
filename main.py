from fastapi import FastAPI
from pydantic import BaseModel
from database_app import crud, models, database

app = FastAPI()


class Request(BaseModel):
    query: str
    location: str = None
    salary: int = None


@app.get("/")
async def read_root():
    return {"data": "Welcome to JobJob"}


@app.get("/about")
async def home():
    return {"data": "Our story innit"}


@app.post("/lookup")
async def trigger_spider(request: Request):
    print(f"Triggering with query {request}")
    return {"data": request}


@app.get("/jobs/{job_id}")
async def get_job(job_id: int):
    session = database.SessionLocal()
    job = crud.get_job(session, job_id)
    return {"job": job}


@app.get("/jobs")
async def get_jobs(limit: int = None):
    session = database.SessionLocal()
    job = crud.get_jobs(session, limit=limit)
    return {"job": job}
