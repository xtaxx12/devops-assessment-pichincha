"""API Manager: emisión y validación de credenciales (API Key y JWT único por transacción)."""

import hmac
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

import jwt

JWT_ALGORITHM = "HS256"
JWT_ISSUER = "api-manager"


@dataclass(frozen=True)
class IssuedToken:
    token: str
    transaction_id: str
    expires_in: int


class TokenInvalidError(Exception):
    pass


class TokenAlreadyUsedError(Exception):
    pass


class ApiKeyValidator:
    def __init__(self, expected_key: str) -> None:
        self._expected_key = expected_key

    def is_valid(self, candidate: str | None) -> bool:
        if candidate is None:
            return False
        # compare_digest evita ataques de temporización al comparar secretos.
        return hmac.compare_digest(self._expected_key, candidate)


class TransactionRegistry(Protocol):
    def mark_consumed(self, transaction_id: str) -> bool:
        """Devuelve True si la transacción no había sido usada; False si ya se consumió."""


class InMemoryTransactionRegistry:
    def __init__(self) -> None:
        self._consumed: set[str] = set()
        self._lock = threading.Lock()

    def mark_consumed(self, transaction_id: str) -> bool:
        with self._lock:
            if transaction_id in self._consumed:
                return False
            self._consumed.add(transaction_id)
            return True


class JwtManager:
    def __init__(
        self,
        secret: str,
        ttl_seconds: int,
        registry: TransactionRegistry | None = None,
    ) -> None:
        self._secret = secret
        self._ttl = timedelta(seconds=ttl_seconds)
        self._registry = registry or InMemoryTransactionRegistry()

    @property
    def ttl_seconds(self) -> int:
        return int(self._ttl.total_seconds())

    def issue(self) -> IssuedToken:
        now = datetime.now(UTC)
        transaction_id = str(uuid.uuid4())
        claims = {
            "jti": transaction_id,
            "iss": JWT_ISSUER,
            "iat": now,
            "exp": now + self._ttl,
        }
        token = jwt.encode(claims, self._secret, algorithm=JWT_ALGORITHM)
        return IssuedToken(token=token, transaction_id=transaction_id, expires_in=self.ttl_seconds)

    def consume(self, token: str) -> dict[str, Any]:
        claims = self._decode(token)
        if not self._registry.mark_consumed(claims["jti"]):
            raise TokenAlreadyUsedError(claims["jti"])
        return claims

    def _decode(self, token: str) -> dict[str, Any]:
        try:
            return jwt.decode(
                token,
                self._secret,
                algorithms=[JWT_ALGORITHM],
                issuer=JWT_ISSUER,
                options={"require": ["jti", "exp", "iat", "iss"]},
            )
        except jwt.PyJWTError as error:
            raise TokenInvalidError(str(error)) from error
