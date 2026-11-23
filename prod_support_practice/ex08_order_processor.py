
import csv
import logging
import sys
import math
from pathlib import Path
from decimal import Decimal, InvalidOperation
from logging.handlers import RotatingFileHandler


# --------------------------------------------------
# 1. SETUP LOGGING
# --------------------------------------------------

def setup_logging():

    logger = logging.getLogger("orders")

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # Avoid duplicate handlers if setup_logging is called again
    if logger.handlers:
        logger.handlers.clear()

    # Common log format
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    # Console handler: INFO and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # File handler: DEBUG and above, with rotation
    file_handler = RotatingFileHandler(
        "app.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8"
    )

    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# --------------------------------------------------
# 2. VALIDATE EACH ORDER
# --------------------------------------------------

def validate_order(row):

    errors = []

    # Validate customer
    customer = row.get("customer")

    if not customer or not customer.strip():
        errors.append("Customer is missing")

    # Validate amount
    amount = None
    amount_text = row.get("amount")

    try:
        if not amount_text:
            raise InvalidOperation

        amount = Decimal(amount_text.replace(",", "").strip())

        if not amount.is_finite() or amount <= 0:
            errors.append("Amount must be a positive number")

    except (InvalidOperation, ValueError, AttributeError):
        errors.append("Amount must be numeric")

    # Validate status
    status = row.get("status")

    if not status or status.strip().upper() not in (
        "PAID", "PENDING", "FAILED"
    ):
        errors.append("Invalid status")

    return errors, amount


# --------------------------------------------------
# 3. PROCESS CSV FILE
# --------------------------------------------------

def process_orders(file_path, logger):

    valid_count = 0
    invalid_count = 0
    total_amount = Decimal("0.00")

    required_headers = [
        "order_id",
        "customer",
        "amount",
        "status"
    ]

    with open(file_path, "r", encoding="utf-8-sig", newline="") as file:

        #This reads CSV data as dictionaries.
        reader = csv.DictReader(file)

        # Validate CSV header
        if reader.fieldnames != required_headers:
            raise ValueError(
                f"Invalid CSV header. Expected {required_headers}, "
                f"but received {reader.fieldnames}"
            )

        for row in reader:

            line_number = reader.line_num

            errors, amount = validate_order(row)

            if errors:

                invalid_count += 1

                reason = "; ".join(errors)

                logger.warning(
                    "Invalid order at line %d: %s",
                    line_number,
                    reason
                )

            else:

                valid_count += 1
                total_amount += amount

                logger.debug(
                    "Valid order: %s",
                    row["order_id"]
                )

    # Final summary
    logger.info("Order processing completed")
    logger.info("Valid orders: %d", valid_count)
    logger.info("Invalid orders: %d", invalid_count)
    logger.info("Total valid order amount: %.2f", total_amount)

    if invalid_count > 0:
        return 1

    return 0


# --------------------------------------------------
# 4. MAIN FUNCTION - HANDLE EXCEPTIONS
# --------------------------------------------------

def main():

    logger = setup_logging()

    file_path = Path(__file__).with_name("orders.csv")

    try:

        logger.info("Starting order file processing")

        exit_code = process_orders(file_path, logger)

        return exit_code

    except FileNotFoundError:

        logger.error("Input file not found: %s", file_path)

        return 2

    except Exception:

        logger.exception(
            "Unexpected error occurred during order processing"
        )

        return 3


# --------------------------------------------------
# 5. PROGRAM ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":

    exit_code = main()

    logger = logging.getLogger("orders")

    logger.info("Program finished with exit code: %d", exit_code)

    logging.shutdown()

    sys.exit(exit_code)
