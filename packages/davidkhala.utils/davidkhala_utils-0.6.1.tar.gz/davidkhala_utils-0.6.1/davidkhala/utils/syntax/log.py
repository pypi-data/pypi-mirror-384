import logging
import os
import sys


class AbstractIngestion:

    def __init__(self, handler: logging.Handler):
        self.handler = handler

    def attach(self, logger: logging.Logger):
        logger.addHandler(self.handler)

    def detach(self, logger: logging.Logger):
        logger.removeHandler(self.handler)


def get_logger(name=None, level=logging.DEBUG) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger


class LevelBasedStreamHandler(logging.StreamHandler):
    def emit(self, record):
        # 根据日志级别选择输出流
        if record.levelno >= logging.WARNING:
            self.stream = sys.stderr
        else:
            self.stream = sys.stdout
        super().emit(record)


def file_handler(log_path):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    return logging.FileHandler(log_path, mode='a', encoding='utf-8')
