from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient
from starlette.responses import RedirectResponse


from database_app import crud, database

app = FastAPI()


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
async def trigger_spider(query: str = Form("blue")):
    print(f"Triggering with query {query}")

    url = app.url_path_for("triggered")
    response = RedirectResponse(url=url)
    return response


@app.post("/landed", response_class=HTMLResponse)
async def triggered():
    return """ 
    <html>
        <head>
            <title>jobjob</title>
        </head>
        <body>
            <h1>looking for ur prize innit</h1>
            
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
async def get_jobs(limit: int = None):
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
