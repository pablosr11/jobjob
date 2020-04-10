# import pytest
# from fastapi.testclient import TestClient

# from jobjob.webapp.webapp_api import app


# @pytest.fixture(scope="module")
# def test_webapp_app():
#     client = TestClient(app)
#     yield client  # testing happens here


# def test_get_homepage(test_webapp_app):
#     response = test_webapp_app.get("/")
#     assert response.status_code == 200
#     assert "text/html" in response.headers["content-type"]
#     assert "welcome to jobjob" in response.text



