import logging
import sys

formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

def setup_trigger_logger():
    logger = logging.getLogger("db.triggers")

    logger.propagate = False

    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


