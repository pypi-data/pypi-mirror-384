import logging
import logging.config
import os
from collections.abc import Callable
from typing import Any

from hpyhrtbase import config, hpyhrt_context, log
from hpyhrtbase.utils import IOUtil, Throttle

__all__ = ["init_app_base"]

_init_app_base_done = False


def reset() -> None:
    global _init_app_base_done
    _init_app_base_done = False


def init_app_base(
    config_path: str,
    init_app_default_configs: Callable[[], Any] | None = None,
    check_dir_names: list[str] | None = None,
) -> None:
    """解析config, 配置app特有的缺省配置, 创建缺省目录, 配置log"""
    global _init_app_base_done
    log_prefix = "init_app_base:"

    if _init_app_base_done:
        raise Exception(f"invalid state, _init_app_base_done {_init_app_base_done}")

    _init_app_base_done = True

    pid = os.getpid()

    log_msg = f"{log_prefix} pid {pid}, Enter with config_path {config_path}"
    print(log_msg)
    logging.info(log_msg)

    config_file = IOUtil.find_abs_path(config_path)

    if not config_file:
        raise Exception("Can't find config file")

    root_dir = IOUtil.find_root_dir(config_file, check_dir_names=check_dir_names)

    overrides = f"root_dir={root_dir}"
    overrides = overrides.replace("\\", "\\\\")
    config_inst = config.params_from_file(config_file, overrides)

    hpyhrt_context.set_config_inst(config_inst)

    if init_app_default_configs:
        init_app_default_configs()

    init_base_default_configs(config_inst)

    global_context = hpyhrt_context.get_global_context()
    global_context.throttle = Throttle()

    # Logistics #
    if hasattr(config_inst, "project_dir"):
        IOUtil.maybe_make_dir(config_inst.project_dir)
    if hasattr(config_inst, "data_cache_dir"):
        IOUtil.maybe_make_dir(config_inst.data_cache_dir)
    if hasattr(config_inst, "output_dir"):
        IOUtil.maybe_make_dir(config_inst.output_dir)

    log.setup_logging(config_inst)

    logging.info(f"{log_prefix} Done")


def init_base_default_configs(config_inst: config.Params) -> None:
    if not hasattr(config_inst, "data_dir"):
        config_inst.data_dir = os.path.join(config_inst.root_dir, "data")

    if not hasattr(config_inst, "norm_timeout"):
        config_inst.norm_timeout = 10

    if not hasattr(config_inst, "data_cache_dir"):
        config_inst.data_cache_dir = os.path.join(config_inst.project_dir, "data_cache")

    if not hasattr(config_inst, "output_dir"):
        config_inst.output_dir = os.path.join(config_inst.project_dir, "outputs")
