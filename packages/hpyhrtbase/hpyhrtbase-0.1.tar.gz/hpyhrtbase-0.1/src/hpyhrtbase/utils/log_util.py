import logging
import traceback
from logging.handlers import RotatingFileHandler
from typing import Any, NoReturn

from hpyhrtbase import hpyhrt_context


class LogUtil:
    @staticmethod
    def log_then_rethrown(log_prefix: str, e: Exception) -> NoReturn:
        prefix = "LogUtil"
        if str(e).startswith(prefix):
            raise e
        else:
            err_msg = f"{prefix} {log_prefix} failed: Exception {str(e)}"
            hpyhrt_context.get_robot_logger().error(err_msg)
            hpyhrt_context.get_robot_logger().info(traceback.format_exc())
            raise Exception(err_msg)

    @staticmethod
    def set_console_logger_level(lvl: Any) -> None:
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            if not isinstance(handler, RotatingFileHandler):
                handler.setLevel(lvl)

    @staticmethod
    def set_logger_level(logger_name: str | None, level: Any) -> None:
        logging.getLogger(logger_name).setLevel(level)
