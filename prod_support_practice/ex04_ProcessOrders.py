
def process_orders(records):

    valid_orders = []
    failures = []

    # Process each record individually
    for position, record in enumerate(records, start=1):

        try:
            # Step 1: Get amount from dictionary
            amount = float(record["amount"])

            # Step 2: Check whether amount is positive
            if amount <= 0:
                raise ValueError("Amount must be positive")

            # Step 3: Add converted amount to record
            valid_record = record.copy()
            valid_record["amount"] = amount

            valid_orders.append(valid_record)

        except KeyError:
            failures.append((position, "Amount is missing"))

        except ValueError as e:
            failures.append((position, str(e)))

    return valid_orders, failures


# Test the function

records = [
    {"id": "A1", "amount": "250.50"},
    {"id": "A2", "amount": "abc"},
    {"id": "A3"},
    {"id": "A4", "amount": "-40"},
    {"id": "A5", "amount": "99"},
]

valid_orders, failures = process_orders(records)

print("Valid Orders:")
print(valid_orders)

print("\nFailed Records:")
print(failures)
