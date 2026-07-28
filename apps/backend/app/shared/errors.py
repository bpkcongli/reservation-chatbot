import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None
    retryable: bool = False


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


class ApplicationError(Exception):
    def __init__(
        self,
        *,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        field: str | None = None,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.detail = ErrorDetail(
            code=code,
            message=message,
            field=field,
            retryable=retryable,
        )
        self.status_code = status_code


def error_response(detail: ErrorDetail, status_code: int) -> JSONResponse:
    envelope = ErrorEnvelope(error=detail)
    return JSONResponse(status_code=status_code, content=envelope.model_dump())


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApplicationError)
    async def handle_application_error(_: Request, exc: ApplicationError) -> JSONResponse:
        return error_response(exc.detail, exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        first_error: dict[str, Any] = exc.errors()[0]
        location = first_error.get("loc", ())
        field = ".".join(str(part) for part in location if part not in {"body", "query", "path"})
        detail = ErrorDetail(
            code="REQUEST_VALIDATION_ERROR",
            message="Data permintaan tidak valid.",
            field=field or None,
            retryable=True,
        )
        return error_response(detail, status.HTTP_422_UNPROCESSABLE_CONTENT)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            detail = ErrorDetail(
                code="NOT_FOUND",
                message="Resource tidak ditemukan.",
            )
        else:
            detail = ErrorDetail(
                code="HTTP_ERROR",
                message=str(exc.detail),
            )
        return error_response(detail, exc.status_code)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled application error",
            extra={"method": request.method, "path": request.url.path},
        )
        detail = ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="Terjadi kesalahan internal. Silakan coba lagi.",
            retryable=True,
        )
        return error_response(detail, status.HTTP_500_INTERNAL_SERVER_ERROR)
