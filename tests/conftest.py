from unittest.mock import MagicMock

import pytest
from fastapi import BackgroundTasks
from fastapi.testclient import TestClient

from spider_app.spider_api import app


@pytest.fixture(scope="module")
def test_app():
    client = TestClient(app)
    yield client  # testing happens here

@pytest.fixture(autouse=True)
def no_background_tasks(monkeypatch):
    monkeypatch.setattr(BackgroundTasks, 'add_task', MagicMock)
