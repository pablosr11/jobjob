
def test_get_homepage(test_webapp_app):
    response = test_webapp_app.get("/")
    assert response.status_code == 200