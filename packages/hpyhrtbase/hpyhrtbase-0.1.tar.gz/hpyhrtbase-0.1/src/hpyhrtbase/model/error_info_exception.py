from __future__ import annotations

from enum import IntEnum

from .error_info import ErrorInfo


class ErrorInfoException(Exception):
    def __init__(self, error_info):
        super().__init__()

        self.error_info = error_info

    @classmethod
    def from_enum(cls, err_enum: IntEnum, detail: str | None = None) -> ErrorInfoException:
        error_info = ErrorInfo(code=int(err_enum), message=err_enum.name, detail=detail)
        return ErrorInfoException(error_info)
