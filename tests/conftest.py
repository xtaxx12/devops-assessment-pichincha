import os

import pytest
from fastapi.testclient import TestClient

TEST_API_KEY = "2f5ae96c-b558-4c7b-a590-a501ae1c3f6c"
TEST_JWT_SECRET = "test-secret-with-enough-length-for-hs256"

# Los tests deben ser deterministas: se fijan los valores antes de importar la app,
# ignorando cualquier API_KEY/JWT_SECRET que el entorno (CI, .env) ya tuviera.
os.environ["API_KEY"] = TEST_API_KEY
os.environ["JWT_SECRET"] = TEST_JWT_SECRET
os.environ["JWT_TTL_SECONDS"] = "60"

from devops_service.main import create_app  # noqa: E402

VALID_PAYLOAD = {
    "message": "This is a test",
    "to": "Juan Perez",
    "from": "Rita Asturia",
    "timeToLifeSec": 45,
}


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture
def api_key_header() -> dict[str, str]:
    return {"X-Parse-REST-API-Key": TEST_API_KEY}


@pytest.fixture
def issue_jwt(client: TestClient, api_key_header: dict[str, str]):
    def _issue() -> str:
        response = client.post("/api-manager/token", headers=api_key_header)
        assert response.status_code == 201
        return response.json()["token"]

    return _issue


@pytest.fixture
def auth_headers(api_key_header: dict[str, str], issue_jwt) -> dict[str, str]:
    return {**api_key_header, "X-JWT-KWY": issue_jwt()}
