import os
import sys
import logging

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# disable root logger
root_logger = logging.getLogger()
root_logger.disabled = True

# create custom logger
logger = logging.getLogger('hestia_earth.distribution')
logger.removeHandler(sys.stdout)
logger.setLevel(logging.getLevelName(LOG_LEVEL))


def log_to_file(filepath: str):
    """
    By default, all logs are saved into a file with path stored in the env variable `LOG_FILENAME`.
    If you do not set the environment variable `LOG_FILENAME`, you can use this function with the file path.

    Parameters
    ----------
    filepath : str
        Path of the file.
    """
    formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", '
        '"filename": "%(filename)s", "message": "%(message)s"}',
        '%Y-%m-%dT%H:%M:%S%z')
    handler = logging.FileHandler(filepath, encoding='utf-8')
    handler.setFormatter(formatter)
    handler.setLevel(logging.getLevelName(LOG_LEVEL))
    logger.addHandler(handler)


LOG_FILENAME = os.getenv('LOG_FILENAME')
if LOG_FILENAME is not None:
    log_to_file(LOG_FILENAME)
