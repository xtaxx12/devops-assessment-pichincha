from fastapi import APIRouter, Depends, status
from fastapi.responses import PlainTextResponse

from devops_service.schemas import MessageRequest, MessageResponse
from devops_service.security import require_api_key, require_transaction_jwt
from devops_service.services import build_greeting

router = APIRouter(tags=["DevOps"])

NOT_ALLOWED_METHODS = ["GET", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]


@router.post(
    "/DevOps",
    response_model=MessageResponse,
    dependencies=[Depends(require_api_key), Depends(require_transaction_jwt)],
)
def send_message(request: MessageRequest) -> MessageResponse:
    return MessageResponse(message=build_greeting(request))


@router.api_route("/DevOps", methods=NOT_ALLOWED_METHODS, include_in_schema=False)
def reject_other_methods() -> PlainTextResponse:
    return PlainTextResponse("ERROR", status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
