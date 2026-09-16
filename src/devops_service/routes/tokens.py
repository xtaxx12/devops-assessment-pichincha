from typing import Annotated

from fastapi import APIRouter, Depends, status

from devops_service.api_manager import JwtManager
from devops_service.schemas import TokenResponse
from devops_service.security import get_jwt_manager, require_api_key

router = APIRouter(prefix="/api-manager", tags=["API Manager"])


@router.post(
    "/token",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
)
def issue_transaction_token(
    manager: Annotated[JwtManager, Depends(get_jwt_manager)],
) -> TokenResponse:
    issued = manager.issue()
    return TokenResponse(
        token=issued.token,
        transaction_id=issued.transaction_id,
        expires_in=issued.expires_in,
    )
