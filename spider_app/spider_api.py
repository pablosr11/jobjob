from fastapi import BackgroundTasks, FastAPI

from database_app import models
from database_app.database import engine
from spider_app.spider import trigger_spider

app = FastAPI()

models.Base.metadata.create_all(bind=engine)


@app.get("/trigger")
async def trigger(background_tasks: BackgroundTasks, q: str = None):
    print("=====SAPI - triggering spider")
    background_tasks.add_task(trigger_spider, q)
    return {"payload": f"Looking {q}"}


@app.get("/")
async def homepage():
    return {"payload": "Welcome to sapi"}
