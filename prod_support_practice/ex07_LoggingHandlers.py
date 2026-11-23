
import logging
from logging.handlers import RotatingFileHandler


def setup_logging():

    # Step 1: Create logger
    logger = logging.getLogger("orders")

    # Set logger level to DEBUG
    logger.setLevel(logging.DEBUG)

    # Step 2: Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Step 3: Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    # Step 4: Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Step 5: Create rotating file handler
    file_handler = RotatingFileHandler(
        "app.log",
        maxBytes=1024 * 1024,
        backupCount=3
    )

    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Step 6: Attach handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Testing
logger = setup_logging()

logger.debug("This is a DEBUG message")
logger.info("This is an INFO message")
