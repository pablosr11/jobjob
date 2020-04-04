from fastapi import FastAPI, BackgroundTasks
from spider_app import spider

app = FastAPI()

@app.get("/trigger")
async def trigger(background_tasks: BackgroundTasks, q: str = None):
    print("=====SAPI - triggering spider")
    background_tasks.add_task(spider.trigger_spider, q)
    return {f"looking-{q}"}

@app.get("/")
async def homepage():
    return {"payload":"Welcome to sapi"}

if __name__ == "__main__":

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
