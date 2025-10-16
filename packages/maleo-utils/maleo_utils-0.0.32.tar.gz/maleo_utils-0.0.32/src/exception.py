import traceback
from typing import Any
from fastapi.exceptions import (
    HTTPException,
    WebSocketException,
    RequestValidationError,
    WebSocketRequestValidationError,
    ResponseValidationError,
)
from pydantic import ValidationError
from maleo.types.dict import StrToAnyDict
from maleo.types.any import SeqOfAny


def extract_details(
    exc: (
        RequestValidationError
        | WebSocketRequestValidationError
        | ResponseValidationError
        | ValidationError
        | HTTPException
        | Exception
    ),
    *,
    include_traceback: bool = False,
) -> SeqOfAny | StrToAnyDict | Any:
    """
    Extracts structured details from an exception for logging, debugging, or API responses.

    Args:
        exc: The exception instance.
        include_traceback: Whether to include a formatted traceback string.

    Returns:
        A dictionary with the exception's type, message, args, and optionally traceback.
    """

    if isinstance(
        exc,
        (
            RequestValidationError,
            WebSocketRequestValidationError,
            ResponseValidationError,
            ValidationError,
        ),
    ):
        return exc.errors()
    elif isinstance(exc, HTTPException):
        return exc.detail
    elif isinstance(exc, WebSocketException):
        return {"code": exc.code, "reason": exc.reason}

    details: StrToAnyDict = {
        "exc_type": type(exc).__name__,
        "exc_data": {
            "message": str(exc),
            "args": exc.args,
        },
    }
    if include_traceback:
        details["traceback"] = traceback.format_exc()
    return details
