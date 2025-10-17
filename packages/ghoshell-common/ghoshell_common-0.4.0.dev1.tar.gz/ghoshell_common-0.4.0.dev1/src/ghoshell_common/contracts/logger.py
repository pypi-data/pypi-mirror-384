import logging
import warnings
from abc import abstractmethod
from typing import Optional, Protocol
from logging import getLogger
from logging.config import dictConfig
from ghoshell_container import Container, Provider, INSTANCE, IoCContainer
from os import path
import yaml

__all__ = [
    'LoggerItf',
    'WorkspaceLoggerProvider', 'LoggerProvider',
    'config_workspace_logger', 'get_console_logger', 'config_logger_from_yaml', 'get_logger_with_extra',
]


class LoggerItf(Protocol):
    """
    """

    @abstractmethod
    def debug(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'DEBUG'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.debug("Houston, we have a %s", "thorny problem", exc_info=True)
        """
        pass

    @abstractmethod
    def info(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'INFO'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.debug("Houston, we have a %s", "notable problem", exc_info=True)
        """
        pass

    @abstractmethod
    def warning(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'WARNING'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.warning("Houston, we have a %s", "bit of a problem", exc_info=True)
        """
        pass

    @abstractmethod
    def error(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'ERROR'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.error("Houston, we have a %s", "major problem", exc_info=True)
        """
        pass

    @abstractmethod
    def exception(self, msg, *args, exc_info=True, **kwargs):
        """
        Convenience method for logging an ERROR with exception information.
        """
        pass

    @abstractmethod
    def critical(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'CRITICAL'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.critical("Houston, we have a %s", "major disaster", exc_info=True)
        """
        pass

    @abstractmethod
    def log(self, level, msg, *args, **kwargs):
        """
        Log 'msg % args' with the integer severity 'level'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.log(level, "We have a %s", "mysterious problem", exc_info=True)
        """
        pass


class PleshakovFormatter(logging.Formatter):
    # copy from
    # https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
    grey = "\x1b[37;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    green = "\x1b[32;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: green + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class FakeLogger(LoggerItf):
    def debug(self, msg, *args, **kwargs):
        pass

    def info(self, msg, *args, **kwargs):
        pass

    def warning(self, msg, *args, **kwargs):
        pass

    def error(self, msg, *args, **kwargs):
        pass

    def exception(self, msg, *args, exc_info=True, **kwargs):
        pass

    def critical(self, msg, *args, **kwargs):
        pass

    def log(self, level, msg, *args, **kwargs):
        pass


def get_logger_with_extra(name: Optional[str] = None, extra: Optional[dict] = None) -> LoggerItf:
    return logging.LoggerAdapter(getLogger(name), extra=extra)


def config_logger_from_yaml(yaml_conf_path: str) -> None:
    """
    configurate logging by yaml config
    :param yaml_conf_path: absolute path of yaml config file
    """
    if not path.exists(yaml_conf_path):
        return

    with open(yaml_conf_path) as f:
        content = f.read()
    data = yaml.safe_load(content)
    dictConfig(data)


def config_workspace_logger(workspace_dir: str) -> None:
    from os.path import join, exists
    logger_path = join(workspace_dir, "logging.yml")
    if not exists(logger_path):
        warnings.warn("Coco logger not found at '{}'".format(logger_path))
    else:
        config_logger_from_yaml(logger_path)


def get_console_logger(
        name: str,
        extra: Optional[dict] = None,
        debug: bool = False,
) -> LoggerItf:
    logger = getLogger(name)
    if not logger.hasHandlers():
        _console_handler = logging.StreamHandler()
        _console_formatter = PleshakovFormatter()
        _console_handler.setFormatter(_console_formatter)
        logger.addHandler(_console_handler)

    if debug:
        logger.setLevel(logging.DEBUG)
    return logging.LoggerAdapter(logger, extra=extra)


class LoggerProvider(Provider[LoggerItf]):
    """
    注册日志服务, 方便从容器中获取日志实例.
    """

    def __init__(
            self,
            name: str = "ghoshell",
            level: Optional[int] = None,
            extra: Optional[dict] = None,
    ):
        self.name = name
        self.level = level
        self.extra = extra

    def singleton(self) -> bool:
        return True

    def contract(self):
        return LoggerItf

    def factory(self, con: Container) -> Optional[LoggerItf]:
        logger = logging.getLogger(self.name)
        return logging.LoggerAdapter(logger, self.extra)


class WorkspaceLoggerProvider(Provider[LoggerItf]):
    """
    logger from workspace.
    """

    def __init__(self, name: str):
        self.name = name

    def singleton(self) -> bool:
        return True

    def factory(self, con: IoCContainer) -> INSTANCE:
        from ghoshell_common.contracts.workspace import Workspace
        ws = con.force_fetch(Workspace)
        if not ws.configs().exists("logging.yml"):
            return get_console_logger(self.name)
        else:
            logging_config_path = ws.configs().abspath().join("logging.yml")
            config_logger_from_yaml(logging_config_path)
            return logging.getLogger(self.name)
