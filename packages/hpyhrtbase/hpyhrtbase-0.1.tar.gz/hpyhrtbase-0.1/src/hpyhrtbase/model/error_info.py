from __future__ import annotations

from enum import IntEnum

from pydantic import BaseModel


class ErrorInfo(BaseModel):
    code: int
    message: str
    detail: str | None = None

    @classmethod
    def from_enum(cls, err_enum: IntEnum, detail: str | None = None) -> ErrorInfo:
        return ErrorInfo(code=int(err_enum), message=err_enum.name, detail=detail)
