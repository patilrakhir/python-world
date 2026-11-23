
import logging

# Step 1: Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

# Step 2: Create logger
logger = logging.getLogger(__name__)


# Method 1: Log only the error message
try:
    result = 10 / 0

except ZeroDivisionError as e:
    logger.error(e)


# Method 2: Log error with full traceback
try:
    result = 10 / 0

except ZeroDivisionError as e:
    logger.error("Error occurred using exc_info", exc_info=True)


# Method 3: Use logger.exception()
try:
    result = 10 / 0

except ZeroDivisionError as e:
    logger.exception("Error occurred using logger.exception")


# Step 3: Log a variable using %s placeholder
user_id = "USER123"

logger.info("Processing user %s", user_id)
