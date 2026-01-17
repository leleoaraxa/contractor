# app/shared/errors.py
from __future__ import annotations

from typing import Any
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def error_payload(
    *,
    error: str,
    message: str | None = None,
    type: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"error": error}
    if type:
        payload["type"] = type
    if message:
        payload["message"] = message
    if details:
        payload["details"] = details
    return payload


def register_exception_handlers(app: FastAPI) -> None:
    logger = logging.getLogger("errors")

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "detail": error_payload(
                    error="validation_error",
                    type="validation_error",
                    message="request validation failed",
                    details={"errors": exc.errors()},
                )
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled_error",
            extra={"path": str(request.url.path)},
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": error_payload(
                    error="internal_error",
                    type="internal_error",
                    message="internal server error",
                )
            },
        )
