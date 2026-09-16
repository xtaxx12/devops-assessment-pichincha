import pytest
from fastapi.testclient import TestClient

from tests.conftest import VALID_PAYLOAD

pytestmark = pytest.mark.integration

EXPECTED_RESPONSE = {"message": "Hello Juan Perez your message will be send"}


def test_post_with_valid_credentials_returns_greeting(client: TestClient, auth_headers):
    response = client.post("/DevOps", json=VALID_PAYLOAD, headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == EXPECTED_RESPONSE


@pytest.mark.parametrize("method", ["GET", "PUT", "PATCH", "DELETE", "OPTIONS"])
def test_other_methods_return_error_string(client: TestClient, method: str, auth_headers):
    response = client.request(method, "/DevOps", headers=auth_headers)
    assert response.status_code == 405
    assert response.text == "ERROR"


def test_missing_api_key_is_rejected(client: TestClient, issue_jwt):
    response = client.post("/DevOps", json=VALID_PAYLOAD, headers={"X-JWT-KWY": issue_jwt()})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing API key"


def test_wrong_api_key_is_rejected(client: TestClient):
    headers = {"X-Parse-REST-API-Key": "wrong", "X-JWT-KWY": "irrelevant"}
    response = client.post("/DevOps", json=VALID_PAYLOAD, headers=headers)
    assert response.status_code == 401


def test_missing_jwt_is_rejected(client: TestClient, api_key_header):
    response = client.post("/DevOps", json=VALID_PAYLOAD, headers=api_key_header)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing transaction JWT"


def test_tampered_jwt_is_rejected(client: TestClient, api_key_header):
    headers = {**api_key_header, "X-JWT-KWY": "header.payload.signature"}
    response = client.post("/DevOps", json=VALID_PAYLOAD, headers=headers)
    assert response.status_code == 401


def test_jwt_is_single_use(client: TestClient, auth_headers):
    first = client.post("/DevOps", json=VALID_PAYLOAD, headers=auth_headers)
    second = client.post("/DevOps", json=VALID_PAYLOAD, headers=auth_headers)
    assert first.status_code == 200
    assert second.status_code == 401
    assert second.json()["detail"] == "Transaction JWT already used"


def test_invalid_payload_returns_422(client: TestClient, auth_headers):
    response = client.post("/DevOps", json={"message": "x"}, headers=auth_headers)
    assert response.status_code == 422


def test_health_endpoint_is_public(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
