
import logging

# Step 1: Configure logging
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

# Step 2: Write messages at all five levels

logging.debug("This is a debug message")

logging.info("Application started successfully")

logging.warning("Disk space is getting low")

logging.error("Database connection failed")

logging.critical("Application cannot continue")
