from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status

from devops_service.api_manager import (
    ApiKeyValidator,
    JwtManager,
    TokenAlreadyUsedError,
    TokenInvalidError,
)

API_KEY_HEADER = "X-Parse-REST-API-Key"
JWT_HEADER = "X-JWT-KWY"


def get_api_key_validator(request: Request) -> ApiKeyValidator:
    return request.app.state.api_key_validator


def get_jwt_manager(request: Request) -> JwtManager:
    return request.app.state.jwt_manager


def require_api_key(
    validator: Annotated[ApiKeyValidator, Depends(get_api_key_validator)],
    api_key: Annotated[str | None, Header(alias=API_KEY_HEADER)] = None,
) -> None:
    if not validator.is_valid(api_key):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")


def require_transaction_jwt(
    manager: Annotated[JwtManager, Depends(get_jwt_manager)],
    token: Annotated[str | None, Header(alias=JWT_HEADER)] = None,
) -> None:
    if token is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing transaction JWT"
        )
    try:
        manager.consume(token)
    except TokenAlreadyUsedError as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Transaction JWT already used"
        ) from error
    except TokenInvalidError as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing transaction JWT"
        ) from error
