import logging
from typing import Union

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s]: %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
)


def get_logger(name: str) -> Union[logging.Logger, None]:
    """Get a logger with timestamp"""
    return logging.getLogger(name)
