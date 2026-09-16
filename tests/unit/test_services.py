import pytest

from devops_service.schemas import MessageRequest
from devops_service.services import build_greeting

pytestmark = pytest.mark.unit


def test_greeting_addresses_recipient():
    request = MessageRequest(
        message="This is a test", to="Juan Perez", sender="Rita Asturia", timeToLifeSec=45
    )
    assert build_greeting(request) == "Hello Juan Perez your message will be send"


def test_request_accepts_from_alias():
    request = MessageRequest.model_validate(
        {"message": "m", "to": "Ana", "from": "Luis", "timeToLifeSec": 1}
    )
    assert request.sender == "Luis"


@pytest.mark.parametrize("ttl", [0, -5])
def test_request_rejects_non_positive_ttl(ttl: int):
    with pytest.raises(ValueError, match="timeToLifeSec"):
        MessageRequest(message="m", to="Ana", sender="Luis", timeToLifeSec=ttl)
