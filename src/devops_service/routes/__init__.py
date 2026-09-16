from devops_service.routes.devops import router as devops_router
from devops_service.routes.health import router as health_router
from devops_service.routes.tokens import router as tokens_router

__all__ = ["devops_router", "health_router", "tokens_router"]
