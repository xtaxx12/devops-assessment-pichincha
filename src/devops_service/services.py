from devops_service.schemas import MessageRequest


def build_greeting(request: MessageRequest) -> str:
    return f"Hello {request.to} your message will be send"
