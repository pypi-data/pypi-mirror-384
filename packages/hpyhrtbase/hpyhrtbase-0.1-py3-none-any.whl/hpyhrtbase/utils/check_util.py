import json
import math
from typing import Any, NoReturn

from hpyhrtbase import hpyhrt_context
from hpyhrtbase.utils import StrUtil


class CheckUtil:
    @staticmethod
    def assert_for_log(condition: Any, error_message: str) -> None:
        assert condition, error_message

    @staticmethod
    def check_dict_expected(
        expected: dict[str, Any], other: dict[str, Any], ignore_order: bool = False, order_by_key: Any = None
    ) -> bool:
        other_value = None
        list_idx = -1

        for key, local_value in expected.items():
            keys = key.split(".")
            for idx, sub_key in enumerate(keys):
                list_idx_start = sub_key.find("[")

                if list_idx_start >= 0:
                    list_idx_end = sub_key.find("]")
                    list_idx = int(sub_key[list_idx_start + 1 : list_idx_end])
                    sub_key = sub_key[:list_idx_start]

                if idx == 0:
                    other_value = other.get(sub_key, None)
                else:
                    if other_value is None:
                        hpyhrt_context.get_robot_logger().info(
                            f"other doesn't have valid value for key {key}, other \n{StrUtil.pprint(other)}")
                        return False

                    if type(other_value) is str:
                        other_value = json.loads(other_value)

                    other_value = other_value.get(sub_key, None)

                if list_idx_start >= 0:
                    if other_value is None:
                        hpyhrt_context.get_robot_logger().info(
                            f"other doesn't have valid value for key {key}, other \n{StrUtil.pprint(other)}")
                        return False

                    if not isinstance(other_value, list):
                        hpyhrt_context.get_robot_logger().info(
                            f"other key {key} is not list, other \n{StrUtil.pprint(other)}")
                        return False
                    if len(other_value) < list_idx:
                        hpyhrt_context.get_robot_logger().info(
                            f"other key {key} not contain idx {list_idx}, other \n{StrUtil.pprint(other)}")
                        return False
                    other_value = other_value[list_idx]

            if other_value is None and local_value is None:
                return True
            elif other_value is None or local_value is None:
                return False

            if not isinstance(local_value, dict):
                if isinstance(local_value, list) and ignore_order:
                    if isinstance(local_value[0], dict):
                        local_value = sorted(local_value, key=order_by_key)
                        other_value = sorted(other_value, key=order_by_key)
                    else:
                        local_value = sorted(local_value)
                        other_value = sorted(other_value)

                if local_value != other_value:
                    hpyhrt_context.get_robot_logger().info(
                        f"key {key} not match, expect {local_value}, got {other_value}, other \n{StrUtil.pprint(other)}")
                    return False
                continue

            for inner_key in local_value.keys():
                inner_local_value = local_value.get(inner_key)
                inner_other_value = other_value.get(inner_key, None)

                if (
                    isinstance(inner_local_value, list)
                    and isinstance(inner_other_value, list)
                    and ignore_order
                ):
                    if isinstance(inner_local_value[0], dict):
                        inner_local_value = sorted(inner_local_value, key=order_by_key)
                        inner_other_value = sorted(inner_other_value, key=order_by_key)
                    else:
                        inner_local_value = sorted(inner_local_value)
                        inner_other_value = sorted(inner_other_value)

                if inner_local_value != inner_other_value:
                    hpyhrt_context.get_robot_logger().info(
                        f"key {key}.{inner_key} not match, expect {inner_local_value}, got {inner_other_value}")
                    return False

        return True

    @staticmethod
    def check_json(input_str: str) -> bool:
        try:
            json.loads(input_str)
            return True
        except Exception:
            return False

    @staticmethod
    def equal(lhs: Any, rhs: Any) -> bool:
        if isinstance(lhs, float) and isinstance(rhs, float):
            return math.isclose(lhs, rhs, abs_tol=0.0001)
        elif lhs == rhs:
            return True
        return False

    @staticmethod
    def halt(description: str = "halt") -> NoReturn:
        hpyhrt_context.get_robot_logger().error(f"Enter halt: {description}")

        raise Exception(description)
