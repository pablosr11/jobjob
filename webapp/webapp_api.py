import requests
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from jobjob.database_app import crud, models
from jobjob.database_app.database import Base, SessionLocal, engine

app = FastAPI()

# when testing locally, this fails as it tries to access the db from docker instead of from outside
Base.metadata.create_all(bind=engine)

NAME_OF_SPIDER_CONTAINER = "spider"


@app.get("/", response_class=HTMLResponse)
async def homepage():
    print("=====API - HOMEPAGE")
    return """ 
    <html>
        <head>
            <title>jobjob</title>
        </head>
        <body>
            <h1>welcome to jobjob</h1>
            
            <h3>what job u want</h3>
            <form action="/lookup" method="post">
                <input type="text" name="query" placeholder="software engineer">
                <br><br>
                <input type="submit" value="find ma money">
            </form> 
        </body>
    </html> 
    """


@app.post("/lookup")
async def trigger_spider(query: str = Form("")):
    print(f"=====API - Triggering with query: {query}")

    # do we have to create a session everytime we access the db?
    db = SessionLocal()

    if not crud.get_query(db, query):
        print("=====API - request to spider_api")
        requests.get(f"http://{NAME_OF_SPIDER_CONTAINER}:8001/trigger?q={query}")

    # add query to db here
    crud.create_query(db, models.Query(query=query))

    url = app.url_path_for("triggered") + f"?q={query}"
    response = RedirectResponse(url=url, status_code=303)
    
    return response


@app.get("/landed", response_class=HTMLResponse)
async def triggered(q: str):

    print("=====API - landing after triggering")

    session = SessionLocal()
    skills = crud.get_skills_by_query_from_contents(db=session, query=q)

    if not skills:
        skills = [[f"No skills found for {q}"]]
    return f""" 
    <html>
        <head>
            <title>jobjob</title>
        </head>
        <body>
            <h1>looking for ur prize innit</h1>
            <ul>
            {[f"<li>{x[0]}</li>" for x in skills]}
            </ul>
            <form action="/" method="get">
                <input type="submit" value="SEND ME BACK">
            </form> 
        </body>
    </html>
    """


@app.get("/jobs")
async def get_jobs(limit: int = 5):
    session = SessionLocal()
    job = crud.get_jobs(session, limit=limit)
    return {"job": job}
