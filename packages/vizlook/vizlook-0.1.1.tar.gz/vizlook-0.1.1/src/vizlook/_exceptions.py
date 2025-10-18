import json
from typing import Optional, Dict, Any
from enum import IntEnum


class HttpStatusCode(IntEnum):
    BadRequest = 400
    Unauthorized = 401
    TooManyRequests = 429
    PayAsYouGoLimitExceeded = 432
    InternalServerError = 500


class VizlookError(Exception):
    pass


class APIError(VizlookError):
    message: str
    status_code: int
    path: Optional[str]
    extra: Optional[Dict[str, Any]]

    def __init__(
        self,
        message: str,
        status_code: int,
        *,
        path: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ):
        """
        @param message: error message
        @param status_code: HTTP status code
        @param path: Path that caused the error
        @param extra: Extra error information
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.path = path
        self.extra = extra

    def __str__(self) -> str:
        details = f"Status Code: {self.status_code}\nError Message: {self.message}"
        if self.path:
            details += f"\nPath: {self.path}"
        if self.extra:
            details += f"\nExtra: {json.dumps(self.extra)}"
        return details
