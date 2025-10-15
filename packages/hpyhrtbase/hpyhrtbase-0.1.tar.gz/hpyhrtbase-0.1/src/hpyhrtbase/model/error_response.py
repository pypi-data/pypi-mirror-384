from pydantic import BaseModel

from .error_info import ErrorInfo


class ErrorResponse(BaseModel):
    error: ErrorInfo | None = None
