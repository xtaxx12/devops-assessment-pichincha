import pytest

from devops_service.config import Settings

pytestmark = pytest.mark.unit


def test_settings_read_from_environment(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("API_KEY", "key-from-env")
    monkeypatch.setenv("JWT_SECRET", "secret-from-env")
    monkeypatch.setenv("JWT_TTL_SECONDS", "120")

    settings = Settings()

    assert settings.api_key == "key-from-env"
    assert settings.jwt_secret == "secret-from-env"
    assert settings.jwt_ttl_seconds == 120


def test_settings_require_api_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.setenv("JWT_SECRET", "secret")
    with pytest.raises(ValueError, match="api_key"):
        Settings(_env_file=None)
