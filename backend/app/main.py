import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, status
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.core.redis_client import get_redis
from app.core.exceptions import (
    AppException,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    ValidationError,
    RateLimitError,
    app_exception_handler,
)
from app.core.middleware import setup_middleware
from app.routers import (
    auth,
    employees,
    departments,
    projects,
    tasks,
    attendance,
    reports,
    leaves,
    notifications,
    analytics,
    activity,
    websocket,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event handler for DB connectivity and resource warmup."""
    # Verify database connection
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connectivity verified successfully.")
    except Exception as e:
        logger.warning("Database connectivity check notice: %s", e)

    # Verify Redis connectivity
    r = get_redis()
    if r:
        logger.info("Redis cache client online.")
    else:
        logger.info("Redis offline; utilizing local in-memory fallback store.")

    yield


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title="Jyohar Tech × Innollege Company Management Platform API",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # Register Middlewares (CORS, Request Logging, Rate Limiter)
    setup_middleware(app)

    # Exception Handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(AuthenticationError, app_exception_handler)
    app.add_exception_handler(AuthorizationError, app_exception_handler)
    app.add_exception_handler(NotFoundError, app_exception_handler)
    app.add_exception_handler(ConflictError, app_exception_handler)
    app.add_exception_handler(ValidationError, app_exception_handler)
    app.add_exception_handler(RateLimitError, app_exception_handler)

    # Health check endpoint
    @app.get("/api/v1/health", status_code=status.HTTP_200_OK, tags=["Health"])
    def health_check():
        return {
            "status": "ok",
            "company": settings.COMPANY_NAME,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # Include API Routers under /api/v1
    api_v1_routers = [
        auth.router,
        employees.router,
        departments.router,
        projects.router,
        tasks.router,
        attendance.router,
        reports.router,
        leaves.router,
        notifications.router,
        analytics.router,
        activity.router,
    ]
    for router in api_v1_routers:
        app.include_router(router, prefix="/api/v1")

    # WebSocket router mounted at root level (/ws)
    app.include_router(websocket.router)

    return app


app = create_app()
