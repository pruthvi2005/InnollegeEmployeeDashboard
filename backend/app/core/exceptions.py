from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "Internal server error",
        error_code: str = "INTERNAL_ERROR",
        extra: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        self.extra = extra or {}


class AuthenticationError(AppException):
    """401 Unauthorized exception."""

    def __init__(
        self,
        detail: str = "Could not validate credentials",
        error_code: str = "AUTHENTICATION_FAILED",
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code=error_code,
        )


class AuthorizationError(AppException):
    """403 Forbidden exception."""

    def __init__(
        self,
        detail: str = "Permission denied for this operation",
        error_code: str = "PERMISSION_DENIED",
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code,
        )


class NotFoundError(AppException):
    """404 Not Found exception."""

    def __init__(
        self,
        detail: str = "Requested resource not found",
        error_code: str = "RESOURCE_NOT_FOUND",
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code=error_code,
        )


class ConflictError(AppException):
    """409 Conflict exception."""

    def __init__(
        self,
        detail: str = "Resource state conflict",
        error_code: str = "RESOURCE_CONFLICT",
    ):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            error_code=error_code,
        )


class ValidationError(AppException):
    """422 Validation Error exception."""

    def __init__(
        self,
        detail: str = "Invalid input data",
        error_code: str = "VALIDATION_ERROR",
        extra: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code=error_code,
            extra=extra,
        )


class RateLimitError(AppException):
    """429 Too Many Requests exception."""

    def __init__(
        self,
        detail: str = "Rate limit exceeded. Please try again later.",
        error_code: str = "RATE_LIMIT_EXCEEDED",
    ):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code=error_code,
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Universal handler for custom application exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": exc.error_code,
            "error": {
                "code": exc.error_code,
                "message": exc.detail,
                "extra": exc.extra,
            },
        },
    )
