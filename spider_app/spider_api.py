from fastapi import BackgroundTasks, FastAPI

from jobjob.spider_app.spider import trigger_spider

app = FastAPI()


@app.get("/trigger")
async def trigger(background_tasks: BackgroundTasks, q: str = None):
    print("=====SAPI - triggering spider")
    background_tasks.add_task(trigger_spider, q)
    return {"payload": f"Looking {q}"}


@app.get("/")
async def homepage():
    return {"payload": "Welcome to sapi"}
