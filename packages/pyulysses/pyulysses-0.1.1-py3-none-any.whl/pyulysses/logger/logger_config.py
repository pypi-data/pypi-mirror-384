import logging
from datetime import datetime, timezone

current_timestamp = datetime.utcnow().isoformat()


def setup_logger(name: str = 'default-logger') -> logging.Logger:
    """
    Sets up a logger that outputs logs to the console only.

    Args:
        name (str): The name of the logger (default is "default-logger").

    Returns:
        logging.Logger: Configured logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)

    if not logger.handlers:
        logger.addHandler(stream_handler)

    return logger
