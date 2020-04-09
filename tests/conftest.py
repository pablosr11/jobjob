# docker run --rm --name db-pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 -v $HOME/repos/z-pablo/thejobjob/.docker_volumes/postgres:/var/lib/postgresql/data -d postgres:12
from unittest.mock import MagicMock

import pytest
from fastapi import BackgroundTasks
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from jobjob.database_app.database import create_db_str, db_config
from jobjob.spider_app.spider_api import app as spider_app
from jobjob.webapp.webapp_api import app as webapp_app

db_config["name"] = "test_db"
engine = create_engine(create_db_str(db_config), echo=True)

@pytest.fixture(scope="module")
def test_spider_app():
    client = TestClient(spider_app)
    yield client  # testing happens here

@pytest.fixture(scope="module")
def test_webapp_app():
    client = TestClient(webapp_app)
    yield client  # testing happens here

@pytest.fixture(autouse=True)
def no_background_tasks(monkeypatch):
    monkeypatch.setattr(BackgroundTasks, 'add_task', MagicMock)
