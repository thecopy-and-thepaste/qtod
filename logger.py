import os
import sys

import logging
from pathlib import Path

DEST_PATH = Path("./logs")

if not DEST_PATH.exists():
    DEST_PATH.mkdir()

LOG_NAME = "log.log"
LOG_FILENAME = Path(f"{str(DEST_PATH)}/{LOG_NAME}")

LOG_FORMAT = "%(asctime)s [%(name)-12s] [%(levelname)-5.5s]  %(message)s"
DEFAULT_LEVEL = logging.INFO

log_formatter = logging.Formatter(LOG_FORMAT)
logging.basicConfig(stream=sys.stderr, format=LOG_FORMAT)


DEBUG_LEVEL = logging.info



def get_logger(name, path: str = LOG_FILENAME,
        level: int = DEFAULT_LEVEL):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    filename = path
    fileHandler = logging.FileHandler(filename, mode='a')
    fileHandler.setFormatter(log_formatter)
    logger.addHandler(fileHandler)

    return logger

debugger = get_logger("DEBUG")
    