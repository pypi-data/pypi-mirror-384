import logging
from typing import Optional

from colorlog import ColoredFormatter

def initialize_logging(log_level: Optional[str]):
    if log_level is None or not isinstance(log_level, str):
        log_level = "INFO"

    handler = logging.StreamHandler()
    formatter = ColoredFormatter(
        "%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(threadName)s: %(white)s%(message)s",
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    )
    handler.setFormatter(formatter)
    logging.basicConfig(handlers=[handler], level=log_level.upper())