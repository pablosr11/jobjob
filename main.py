from fastapi import FastAPI, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.testclient import TestClient

import requests
from database_app import crud, database, models

app = FastAPI()


def append_query(func_name: str, query: str):
    """Returns a full url for a given function with a query parameter """
    return app.url_path_for(func_name) + f"?q={query}"


@app.get("/", response_class=HTMLResponse)
async def homepage():
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
async def trigger_spider(query: str = Form("junior")):
    print(f"Triggering with query {query}")

    # do we have to create a session everytime we access the db?
    db = database.SessionLocal()

    if not crud.get_query(db, query):
        requests.get(f"http://0.0.0.0:8001/trigger?q={query}")

    # add query to db here
    crud.create_query(db, models.Query(query=query)) 

    url = append_query("triggered", query)
    response = RedirectResponse(url=url, status_code=303)
    return response


@app.get("/landed", response_class=HTMLResponse)
async def triggered(q: str):
    session = database.SessionLocal()

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


@app.get("/jobs/{job_id}")
async def get_job(job_id: int):
    session = database.SessionLocal()
    job = crud.get_job(session, job_id)
    return {"job": job}


@app.get("/jobs")
async def get_jobs(limit: int = 5):
    session = database.SessionLocal()
    job = crud.get_jobs(session, limit=limit)
    return {"job": job}


test_client = TestClient(app)


def test_homepage():
    url = app.url_path_for("homepage")
    response = test_client.get(url)
    assert response.status_code == 200
    assert "welcome to jobjob" in response.text


# def test_redirect_after_trigger():
#     url = app.url_path_for("trigger_spider")
#     response = test_client.post(url, json={"query":"testing_redirect"})
#     assert response.status_code == 307
#     assert "looking for ur prize innit" in response.text


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
