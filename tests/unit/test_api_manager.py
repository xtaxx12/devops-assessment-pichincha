import jwt
import pytest

from devops_service.api_manager import (
    ApiKeyValidator,
    InMemoryTransactionRegistry,
    JwtManager,
    TokenAlreadyUsedError,
    TokenInvalidError,
)

pytestmark = pytest.mark.unit

SECRET = "unit-test-secret-0123456789abcdef"


@pytest.fixture
def manager() -> JwtManager:
    return JwtManager(secret=SECRET, ttl_seconds=60, registry=InMemoryTransactionRegistry())


class TestApiKeyValidator:
    def test_accepts_matching_key(self):
        assert ApiKeyValidator(expected_key="abc").is_valid("abc")

    def test_rejects_different_key(self):
        assert not ApiKeyValidator(expected_key="abc").is_valid("abd")

    def test_rejects_missing_key(self):
        assert not ApiKeyValidator(expected_key="abc").is_valid(None)


class TestJwtManager:
    def test_issued_token_carries_its_transaction_id(self, manager: JwtManager):
        issued = manager.issue()
        claims = manager.consume(issued.token)
        assert claims["jti"] == issued.transaction_id
        assert issued.expires_in == 60

    def test_each_issued_token_is_unique(self, manager: JwtManager):
        assert manager.issue().token != manager.issue().token

    def test_token_cannot_be_reused(self, manager: JwtManager):
        token = manager.issue().token
        manager.consume(token)
        with pytest.raises(TokenAlreadyUsedError):
            manager.consume(token)

    def test_rejects_token_signed_with_other_secret(self, manager: JwtManager):
        other = JwtManager(secret="another-secret-0123456789abcdef!", ttl_seconds=60)
        with pytest.raises(TokenInvalidError):
            manager.consume(other.issue().token)

    def test_rejects_expired_token(self):
        expired_manager = JwtManager(secret=SECRET, ttl_seconds=-1)
        with pytest.raises(TokenInvalidError):
            expired_manager.consume(expired_manager.issue().token)

    def test_rejects_malformed_token(self, manager: JwtManager):
        with pytest.raises(TokenInvalidError):
            manager.consume("not-a-jwt")

    def test_rejects_token_without_transaction_id(self, manager: JwtManager):
        token = jwt.encode({"iss": "api-manager"}, SECRET, algorithm="HS256")
        with pytest.raises(TokenInvalidError):
            manager.consume(token)


class TestInMemoryTransactionRegistry:
    def test_first_mark_succeeds_second_fails(self):
        registry = InMemoryTransactionRegistry()
        assert registry.mark_consumed("tx-1") is True
        assert registry.mark_consumed("tx-1") is False
