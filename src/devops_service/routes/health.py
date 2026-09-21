from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from devops_service import __version__
from devops_service.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)
