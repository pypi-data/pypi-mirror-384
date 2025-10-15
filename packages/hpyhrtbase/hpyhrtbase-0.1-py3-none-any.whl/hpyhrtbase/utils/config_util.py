from typing import Any

from hpyhrtbase import hpyhrt_context


class ConfigUtil:
    @staticmethod
    def decode_invisible_config(orig_value: str, must_exist: bool = True) -> Any:
        """
        有些配置项含有敏感信息，为了打印log时候不打印它们，
        我们加了一层重定向，如果配置项有指定前缀，则真实
        配置存在重定向对应key下
        """
        config_inst = hpyhrt_context.get_config_inst()
        invisible_config_prefix = config_inst.invisible_config_prefix

        if orig_value.startswith(invisible_config_prefix):
            to_value = None

            prefix_len = len(invisible_config_prefix)

            config_key = orig_value[prefix_len:]

            if config_key != "" and hasattr(config_inst, config_key):
                to_value = config_inst[config_key]
            elif must_exist:
                raise Exception(f"{config_key} was not configured")

            return to_value
        else:
            return orig_value

    @staticmethod
    def override_config(config: Any, orig_value: str, key_prefix: str) -> tuple[str | None, Any]:
        """
        有些配置项含有敏感信息，为了打印log时候不打印它们，
        我们加了一层重定向，如果配置项有指定前缀，则真实
        配置存在重定向对应key下
        """
        if orig_value.startswith(key_prefix):
            to_value = None

            prefix_len = len(key_prefix)

            config_key = orig_value[prefix_len:]

            if config_key != "" and hasattr(config, config_key):
                to_value = config[config_key]

            return config_key, to_value
        else:
            return None, orig_value
