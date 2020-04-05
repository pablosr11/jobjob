from unittest.mock import MagicMock

import pytest
from fastapi import BackgroundTasks
from fastapi.testclient import TestClient

from spider_app.spider_api import app


@pytest.fixture(autouse=True)
def no_background_tasks(monkeypatch):
    monkeypatch.setattr(BackgroundTasks, 'add_task', MagicMock)

client = TestClient(app)

def test_get_homepage():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"payload":"Welcome to sapi"}

def test_trigger_spider_with_query(no_background_tasks):
    query = "ham"
    response = client.get(f"/trigger?q={query}")
    assert response.status_code == 200
    assert response.json() == {"payload":f"Looking {query}"}

def test_trigger_spider_without_query(no_background_tasks):
    response = client.get(f"/trigger")
    assert response.status_code == 200
    assert response.json() == {"payload": "Looking None"}
