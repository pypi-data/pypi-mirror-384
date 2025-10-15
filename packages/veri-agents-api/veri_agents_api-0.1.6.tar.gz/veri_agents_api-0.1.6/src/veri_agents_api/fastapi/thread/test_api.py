import json
from fastapi.testclient import TestClient

def test_openapi_snapshot(simple_client: TestClient, snapshot):
    response = simple_client.get("/openapi.json")
    assert response.status_code == 200
    assert json.dumps(response.json(), indent=2) == snapshot
