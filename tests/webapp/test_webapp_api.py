import json
from unittest.mock import MagicMock

import pytest
import requests
from fastapi.testclient import TestClient

from jobjob.database_app import crud
from jobjob.webapp.webapp_api import app


@pytest.fixture(scope="module")
def test_webapp_app():
    client = TestClient(app)
    yield client  # testing happens here


def test_get_homepage(test_webapp_app):
    response = test_webapp_app.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "welcome to jobjob" in response.text

def test_trigger_spider(test_webapp_app, monkeypatch):
    # prepare what we ened
    test_request_data = {"query": "query for trigger spider"}

    monkeypatch.setattr(requests, "get", MagicMock())
    monkeypatch.setattr(crud, "create_query", MagicMock())
    monkeypatch.setattr(crud, "get_query", MagicMock(return_value=0))

    # call endpoint
    response = test_webapp_app.post("/lookup", data=json.dumps(test_request_data))

    # assert
    assert response.status_code == 303 # redirected

def test_landed_after_triggering(test_webapp_app, monkeypatch):

    monkeypatch.setattr(crud, "get_skills_by_query_from_contents", MagicMock(return_value=[]))

    response = test_webapp_app.get("/landed?q=blabla")

    assert response.status_code == 200
    assert "looking for ur prize innit" in response.text

def test_get_jobs(test_webapp_app, monkeypatch):

    monkeypatch.setattr(crud, "get_jobs", MagicMock())

    response = test_webapp_app.get("/jobs")

    assert response.status_code == 200
    assert "job" in response.json()
