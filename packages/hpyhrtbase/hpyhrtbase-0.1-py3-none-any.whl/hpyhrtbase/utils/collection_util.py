from typing import Any, Literal


class CollectionUtil:
    @staticmethod
    def dict_extract_by_keys(in_dict: dict[str, Any], key_list: list[str]) -> dict[str, Any]:
        target_dict = {}

        for key in key_list:
            if key in in_dict:
                target_dict[key] = in_dict[key]

        return target_dict

    @staticmethod
    def dict_get_by_path(key_path: str, cur_ns: dict[str, Any]) -> tuple[Any, bool]:
        key_path_items = key_path.split(".")

        for i in range(len(key_path_items) - 1):
            if key_path_items[i] not in cur_ns or not isinstance(cur_ns[key_path_items[i]], dict):
                return None, False
            cur_ns = cur_ns[key_path_items[i]]

        return cur_ns.get(key_path_items[-1]), True

    @staticmethod
    def dict_ensure_key_path(key_path: str, cur_ns: dict[str, Any]) -> tuple[str, Any]:
        key_path_items = key_path.split(".")

        for i in range(len(key_path_items) - 1):
            if key_path_items[i] not in cur_ns or cur_ns[key_path_items[i]] is None:
                cur_ns[key_path_items[i]] = {}
            cur_ns = cur_ns[key_path_items[i]]

        return key_path_items[-1], cur_ns

    @staticmethod
    def dict_update_if_not_exist(target: dict[str, Any], source: dict[str, Any], keys: list[str]) -> None:
        for key in keys:
            if key not in target and key in source:
                target[key] = source[key]

    @staticmethod
    def dict_update_on_mode(target: dict[str, Any], other: dict[str, Any], mode: Literal["override", "merge"] = "override") -> None:
        if mode == "override":
            target.update(other)
        elif mode == "merge":
            for key, value in other.items():
                if key not in target:
                    target[key] = value
                elif not (isinstance(target[key], dict) and isinstance(value, dict)):
                    target[key] = value
                else:
                    CollectionUtil.dict_update_on_mode(target[key], value, mode)
        else:
            raise Exception(f"invalid mode {mode}")
