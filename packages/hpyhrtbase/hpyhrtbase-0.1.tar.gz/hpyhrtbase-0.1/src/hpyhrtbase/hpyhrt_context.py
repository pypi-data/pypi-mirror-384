from types import SimpleNamespace
from typing import Any

from hpyhrtbase.config import Params

config_inst: Params | None = None
global_context: Any = SimpleNamespace()


def reset() -> None:
    global config_inst, global_context
    config_inst = None
    global_context = SimpleNamespace()


def get_global_context() -> Any:
    return global_context


def set_config_inst(inst: Params) -> None:
    global config_inst
    config_inst = inst


def get_config_inst() -> Params:
    global config_inst

    if config_inst is None:
        raise ValueError("config not parsed yet?")

    return config_inst
