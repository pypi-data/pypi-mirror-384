from typing import Any


class ObjectUtil:
    @staticmethod
    def setattr_if_not_exist(obj: object, name: str, value: Any) -> None:
        if not hasattr(obj, name):
            setattr(obj, name, value)
