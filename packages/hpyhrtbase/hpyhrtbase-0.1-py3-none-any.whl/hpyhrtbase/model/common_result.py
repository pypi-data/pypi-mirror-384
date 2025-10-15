from typing import Generic, TypeVar

from .error_response import ErrorResponse

DataType = TypeVar("DataType")

class CommonResult(ErrorResponse, Generic[DataType]):
    data: DataType | None = None
