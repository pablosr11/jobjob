
def test_get_homepage(test_app):
    response = test_app.get("/")
    assert response.status_code == 200
    assert response.json() == {"payload":"Welcome to sapi"}

def test_trigger_spider_with_query(test_app):
    query = "ham"
    response = test_app.get(f"/trigger?q={query}")
    assert response.status_code == 200
    assert response.json() == {"payload":f"Looking {query}"}

def test_trigger_spider_without_query(test_app):
    default_query = None
    response = test_app.get(f"/trigger")
    assert response.status_code == 200
    assert response.json() == {"payload": f"Looking {default_query}"}
