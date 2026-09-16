import jwt
import pytest
from fastapi.testclient import TestClient

from tests.conftest import TEST_JWT_SECRET

pytestmark = pytest.mark.integration


def test_token_endpoint_issues_signed_jwt(client: TestClient, api_key_header):
    response = client.post("/api-manager/token", headers=api_key_header)
    assert response.status_code == 201
    body = response.json()
    claims = jwt.decode(body["token"], TEST_JWT_SECRET, algorithms=["HS256"])
    assert claims["jti"] == body["transaction_id"]
    assert body["expires_in"] == 60


def test_token_endpoint_requires_api_key(client: TestClient):
    response = client.post("/api-manager/token")
    assert response.status_code == 401


def test_tokens_are_unique_per_request(client: TestClient, issue_jwt):
    assert issue_jwt() != issue_jwt()
