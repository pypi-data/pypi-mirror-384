import copy
import logging
import logging.config
import os
from logging.handlers import RotatingFileHandler
from typing import Any, cast

from hpyhrtbase import config
from hpyhrtbase.utils import IOUtil


def setup_logging(config_inst: config.Params) -> None:
    init_log_default_configs(config_inst)

    log_dir = config_inst.log_dir

    error_file_handler_on = True
    error_file_handler_idx = -1
    file_handler_on = True
    file_handler_idx = -1
    console_on = True

    log_config = copy.deepcopy(log_config_default)

    if "error_file_handler" in config_inst.log_handlers:
        handler_config = log_config["handlers"]["error_file_handler"]
        handler_config["filename"] = os.path.join(log_dir, "app_error.log")
        handler_config["backupCount"] = config_inst.log_backupCount
    else:
        del log_config["handlers"]["error_file_handler"]
        log_config["root"]["handlers"].remove("error_file_handler")
        error_file_handler_on = False

    if "file_handler" in config_inst.log_handlers:
        handler_config = log_config["handlers"]["file_handler"]
        handler_config["filename"] = os.path.join(log_dir, "app.log")
        handler_config["backupCount"] = config_inst.log_backupCount
    else:
        del log_config["handlers"]["file_handler"]
        log_config["root"]["handlers"].remove("file_handler")
        file_handler_on = False

    if "console" not in config_inst.log_handlers:
        del log_config["handlers"]["console"]
        log_config["root"]["handlers"].remove("console")
        console_on = False

    if not (error_file_handler_on or file_handler_on or console_on):
        raise Exception("at least enable one log handler")

    logging.config.dictConfig(log_config)
    root_logger = logging.getLogger()

    handler_idx = 0

    if console_on:
        handler_idx = 1

    if file_handler_on:
        file_handler_idx = handler_idx
        handler_idx += 1

    if error_file_handler_on:
        error_file_handler_idx = handler_idx

    if error_file_handler_idx >= 0:
        log_path = log_config["handlers"]["error_file_handler"]["filename"]
        if os.path.exists(log_path) and os.stat(log_path).st_size != 0:
            file_handler = cast(RotatingFileHandler, root_logger.handlers[error_file_handler_idx])
            file_handler.doRollover()

    if file_handler_idx >= 0:
        log_path = log_config["handlers"]["file_handler"]["filename"]
        if os.path.exists(log_path) and os.stat(log_path).st_size != 0:
            file_handler = cast(RotatingFileHandler, root_logger.handlers[file_handler_idx])
            file_handler.doRollover()

    if "logger_levels" in config_inst:
        for logger_level in config_inst.logger_levels:
            logging.getLogger(logger_level[0]).setLevel(logger_level[1])

    logging.debug("debug: App start logging")
    logging.info("info: App start logging")


def init_log_default_configs(config_inst: config.Params) -> None:
    if not hasattr(config_inst, "log_backupCount"):
        config_inst.log_backupCount = 20

    if not hasattr(config_inst, "log_dir"):
        config_inst.log_dir = os.path.join(config_inst.project_dir, "logs")

    if not hasattr(config_inst, "log_handlers"):
        config_inst.log_handlers = ["console", "file_handler", "error_file_handler"]

    if hasattr(config_inst, "log_dir"):
        IOUtil.maybe_make_dir(config_inst.log_dir)


log_config_default: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "brief": {
            "class": "logging.Formatter",
            "format": "%(asctime)s.%(msecs)03d line%(lineno)s %(levelname)s %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "normal": {
            "class": "logging.Formatter",
            "format": "%(asctime)s.%(msecs)03d  %(levelname)-8s [%(name)s] %(funcName)s:%(lineno)d: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "verbose": {
            "class": "logging.Formatter",
            "format": "%(asctime)s.%(msecs)03d  %(levelname)-8s [%(name)s] %(module)s:%(funcName)s:%(lineno)d: [%(process)d]: %(threadName)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "normal",
            "stream": "ext://sys.stdout",
        },
        "file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "normal",
            "filename": "app.log",
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8",
        },
        "error_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "normal",
            "filename": "app_error.log",
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8",
        },
    },
    "loggers": {},
    "root": {
        "handlers": ["console", "file_handler", "error_file_handler"],
        "level": "INFO",
    },
}
