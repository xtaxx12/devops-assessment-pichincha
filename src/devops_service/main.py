from fastapi import FastAPI

from devops_service import __version__
from devops_service.api_manager import ApiKeyValidator, JwtManager
from devops_service.config import Settings, get_settings
from devops_service.routes import devops_router, health_router, tokens_router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title=settings.app_name, version=__version__)
    app.state.api_key_validator = ApiKeyValidator(expected_key=settings.api_key)
    app.state.jwt_manager = JwtManager(
        secret=settings.jwt_secret, ttl_seconds=settings.jwt_ttl_seconds
    )
    app.include_router(health_router)
    app.include_router(tokens_router)
    app.include_router(devops_router)
    return app


app = create_app()
