import json
from typing import Any


class StrUtil:
    @staticmethod
    def pprint(obj: Any, not_process_str: bool = True) -> str:
        if not obj:
            return str(obj)
        if not_process_str and isinstance(obj, str):
            return obj
        temp = json.dumps(obj, indent=4, ensure_ascii=False, default=str)
        return temp
