from fastapi import FastAPI, BackgroundTasks
import spider

app = FastAPI()


@app.get("/trigger")
async def trigger(background_tasks: BackgroundTasks, q: str = None, l:str = None):
    background_tasks.add_task(spider.trigger_spider, q, l)
    return {f"looking-{q}"}


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
