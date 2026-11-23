# Python Error Handling and Logging: Hands-On Workbook (PyCharm)

Level: intermediate. Work through the exercises in order. Each one builds on the last and ends with a small capstone that looks like real production support work.

**How to use this file:** Read Part 1 (setup and exercises). Write your own solution in PyCharm and run it. Only then look at Part 2 (solutions).

---

## Setup in PyCharm (5 minutes)

1. **File > New Project**, name it `prod_support_practice`. Choose a new virtual environment (the default is fine).
2. Right-click the project folder > **New > Python File**. Create one file per exercise, named like `ex01_divide.py`, `ex02_files.py`, and so on.
3. **Run** a file with the green triangle (or `Shift+F10`).
4. **Debug** a file with the bug icon (or `Shift+F9`). Click in the left gutter next to a line number to set a red breakpoint first.
5. Create a plain text file called `orders.csv` in the project folder when you reach Exercise 8 (the data is given there).
6. To pass command-line arguments: **Run > Edit Configurations**, then fill in *Parameters*.

Tip: keep the **Run** window at the bottom visible. Reading output carefully is part of the skill.

---

# Part 1: Exercises

## Section A: Error Handling

### Exercise 1: try / except / else / finally
Write a function `divide_strings(a_text, b_text)` that:
- Converts both inputs to numbers and divides `a` by `b`.
- Prints a friendly message and returns `None` when the input isn't a number.
- Prints a different message and returns `None` when dividing by zero.
- Returns the result when everything works.
- Always prints "Finished attempt" at the end, whatever happened.

Test with: `("10", "2")`, `("10", "0")`, `("abc", "2")`, `("", "5")`.

**Think about:** Which part belongs in `else`? What happens to `finally` when you `return` inside `try`?

### Exercise 2: Reading a file safely
Write `read_text_file(path)` that returns the file's text, or `None` if something goes wrong. Handle these separately with clear messages:
- File doesn't exist.
- No permission to read it.
- File isn't valid UTF-8.

Test with: a real file, a path that doesn't exist, and a folder path (what exception do you get?).

### Exercise 3: Custom exceptions and exception chaining
Create a config loader `load_config(path)` for a JSON file that must contain `db_host`, `db_port` (an integer), and `timeout`.
- Define your own exception class `ConfigError`.
- If the file is missing, or the JSON is broken, or keys are missing, or `db_port` is not an integer, raise `ConfigError` with a clear message.
- Use `raise ... from e` when converting a lower-level error, so the original cause is preserved.

Test with: a good file, a missing file, a file containing `{bad json`, and a file missing `timeout`.

### Exercise 4: Don't let one bad record stop the batch
You receive a list of order dictionaries:

```python
records = [
    {"id": "A1", "amount": "250.50"},
    {"id": "A2", "amount": "abc"},
    {"id": "A3"},
    {"id": "A4", "amount": "-40"},
    {"id": "A5", "amount": "99"},
]
```

Write `process_orders(records)` that returns two lists: valid orders (with the amount converted to a number) and failures (the record position plus the reason). Rules: amount must exist, be numeric, and be positive. One bad record must never crash the whole run.

**Think about:** Catching several exception types in one `except`. Which one would hide a real bug if you were too broad?

---

## Section B: Logging

### Exercise 5: Your first logger
Create a script that:
- Configures logging with `basicConfig` at DEBUG level and a format that shows time, level, logger name, and message.
- Writes one message at each level (debug, info, warning, error, critical).
- Then change the level to INFO and rerun. What disappears?

### Exercise 6: Logging exceptions properly
Write code that deliberately triggers a `ZeroDivisionError` inside `try/except`, and log it in three ways:
1. `logger.error(e)` (just the message)
2. `logger.error("...", exc_info=True)`
3. `logger.exception("...")`

Compare the outputs. Which one gives you the full traceback? Also practise logging a variable with `%s` placeholders instead of f-strings: `logger.info("Processing user %s", user_id)`.

### Exercise 7: Handlers, formatters, and log rotation
Write a function `setup_logging()` that returns a logger named `"orders"` with:
- A **console** handler showing INFO and above.
- A **file** handler writing DEBUG and above to `app.log`.
- File rotation so the log never grows past about 1 MB, keeping 3 old files.
- A formatter showing time, level, logger name, and message.
- Protection against duplicate log lines if `setup_logging()` is called twice.

Test by logging a DEBUG and an INFO message. Which one appears on screen? Which appears in `app.log`?

---

## Section C: Putting It Together

### Exercise 8 (Capstone): Order file processor
Create `orders.csv` in your project folder:

```
order_id,customer,amount,status
1001,Asha,250.50,PAID
1002,Ravi,abc,PAID
1003,,100,PENDING
1004,Meera,-50,PAID
1005,John,"1,200.00",PAID
1006,Priya,75,UNKNOWN
1007,Karan,310.25,failed
```

Write a script that:
1. Sets up logging (reuse Exercise 7).
2. Reads the CSV and validates each row: customer required, amount numeric and positive (commas allowed), status one of PAID / PENDING / FAILED (case-insensitive).
3. Logs each bad row as a WARNING with its line number and reason, then continues.
4. Logs a final INFO summary: valid count, invalid count, total amount of valid orders.
5. Handles a missing input file with an ERROR log.
6. Logs any unexpected crash with the full traceback.
7. Returns a meaningful exit code: `0` all good, `1` some bad rows, `2` file missing, `3` unexpected failure.

Test: normal run, rename the file to simulate missing, and then add a header typo to see what happens.

### Exercise 9: Read the traceback
No coding. Read this traceback and answer the questions below.

```
Traceback (most recent call last):
  File "/home/user/orders/main.py", line 42, in <module>
    main()
  File "/home/user/orders/main.py", line 35, in main
    total = calculate_total(orders)
  File "/home/user/orders/billing.py", line 12, in calculate_total
    return sum(o["amount"] for o in orders)
  File "/home/user/orders/billing.py", line 12, in <genexpr>
    return sum(o["amount"] for o in orders)
KeyError: 'amount'
```

1. What is the error type and message?
2. In which file and function did it happen?
3. Which line of *your* code started the chain?
4. What is the most likely cause?
5. What would you log or change so the next failure is easier to diagnose?

### Exercise 10: Debugging in PyCharm
Take your Exercise 8 script and:
1. Set a breakpoint inside your validation function.
2. Run in Debug mode and step through one bad row with **F8** (step over) and **F7** (step into).
3. Watch the **Variables** panel as values change.
4. Right-click in the editor > **Evaluate Expression** and test `row.get("amount")`.
5. Right-click the breakpoint and add a **condition** such as `row["customer"] == ""` so it only pauses on the bad row.

---

# Part 2: Solutions

Try the exercises first. Then compare.

## Exercise 1 solution

```python
def divide_strings(a_text, b_text):
    try:
        a = float(a_text)
        b = float(b_text)
        result = a / b
    except ValueError:
        print(f"Invalid number in input: {a_text!r}, {b_text!r}")
        return None
    except ZeroDivisionError:
        print("Cannot divide by zero")
        return None
    else:
        # Runs only if the try block had NO exception
        print("Division succeeded")
        return result
    finally:
        # Runs always, even when we returned above
        print("Finished attempt")


if __name__ == "__main__":
    for pair in [("10", "2"), ("10", "0"), ("abc", "2"), ("", "5")]:
        print(pair, "->", divide_strings(*pair))
```

**Key points**
- `else` holds code that should run only on success. It keeps the `try` block small.
- `finally` runs even when there's a `return` in `try`, `except`, or `else`. It's the place for cleanup.
- Only the risky lines belong in `try`.

---

## Exercise 2 solution

```python
def read_text_file(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"File not found: {path}")
    except PermissionError:
        print(f"No permission to read: {path}")
    except IsADirectoryError:
        print(f"This is a folder, not a file: {path}")
    except UnicodeDecodeError:
        print(f"File is not valid UTF-8: {path}")
    return None
```

**Key points**
- Opening a folder raises `IsADirectoryError` on Linux/macOS and `PermissionError` on Windows. Platform differences are common in production.
- `with` guarantees the file is closed.
- Always pass `encoding=` explicitly. The default depends on the operating system.

---

## Exercise 3 solution

```python
import json


class ConfigError(Exception):
    """Raised when the configuration is missing or invalid."""


REQUIRED_KEYS = ("db_host", "db_port", "timeout")


def load_config(path):
    try:
        with open(path, encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError as e:
        raise ConfigError(f"Config file not found: {path}") from e
    except json.JSONDecodeError as e:
        raise ConfigError(f"Config file is not valid JSON: {e}") from e

    missing = [k for k in REQUIRED_KEYS if k not in config]
    if missing:
        raise ConfigError(f"Missing config keys: {missing}")
    if not isinstance(config["db_port"], int):
        raise ConfigError(f"db_port must be an integer, got {config['db_port']!r}")
    return config


if __name__ == "__main__":
    try:
        cfg = load_config("config.json")
        print("Loaded:", cfg)
    except ConfigError as e:
        print("Config problem:", e)
        print("Original cause:", repr(e.__cause__))
```

**Key points**
- A custom exception lets callers catch *your* kind of failure without catching everything.
- `raise ... from e` keeps the original error attached as `__cause__`, so the traceback shows both. This is exception chaining.
- Validating early gives clear messages instead of a confusing `KeyError` ten functions later.

---

## Exercise 4 solution

```python
def process_orders(records):
    valid, failures = [], []

    for position, rec in enumerate(records, start=1):
        try:
            amount = float(rec["amount"])
            if amount <= 0:
                raise ValueError("amount must be positive")
            valid.append({"id": rec["id"], "amount": amount})
        except (KeyError, ValueError) as e:
            failures.append((position, repr(e)))

    return valid, failures


if __name__ == "__main__":
    records = [
        {"id": "A1", "amount": "250.50"},
        {"id": "A2", "amount": "abc"},
        {"id": "A3"},
        {"id": "A4", "amount": "-40"},
        {"id": "A5", "amount": "99"},
    ]
    good, bad = process_orders(records)
    print("Valid:", good)
    print("Failed:", bad)
```

**Key points**
- The `try` is *inside* the loop, so one failure only skips that record.
- Catch the specific exceptions you expect (`KeyError`, `ValueError`). Catching `Exception` here would also hide genuine bugs, such as a typo in a variable name.
- Return the failures. Don't just discard them, because the caller needs to know data was skipped.
- For real money, use `Decimal` instead of `float`.

---

## Exercise 5 solution

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

logger.debug("Debug: detailed info for developers")
logger.info("Info: normal progress messages")
logger.warning("Warning: something unexpected, but we can continue")
logger.error("Error: an operation failed")
logger.critical("Critical: the application may not be able to continue")
```

Change `level=logging.DEBUG` to `logging.INFO` and the debug line disappears. Levels filter: a logger set to INFO shows INFO, WARNING, ERROR, and CRITICAL.

**Key points**
- `logging.getLogger(__name__)` gives each module its own named logger.
- Production usually runs at INFO. Switch to DEBUG only while investigating.
- `basicConfig` only takes effect the first time it's called in a process.

---

## Exercise 6 solution

```python
import logging

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def risky():
    return 1 / 0


try:
    risky()
except ZeroDivisionError as e:
    logger.error(e)                                  # message only, NO traceback
    logger.error("Calculation failed", exc_info=True)  # message + traceback
    logger.exception("Calculation failed")           # same as error + exc_info, preferred

user_id = 4471
logger.info("Processing user %s", user_id)           # preferred over f-strings in logging
```

**Key points**
- `logger.exception(...)` is the standard way to log inside an `except` block. It logs at ERROR level with the full traceback.
- `logger.error(e)` loses the traceback, which is the most common logging mistake.
- Use `%s` placeholders: the string is only built if that log level is actually enabled.
- `logger.exception` should only be called from inside an `except` block.

---

## Exercise 7 solution

```python
import logging
from logging.handlers import RotatingFileHandler


def setup_logging(log_file="app.log"):
    logger = logging.getLogger("orders")
    logger.setLevel(logging.DEBUG)       # the logger lets everything through...
    logger.handlers.clear()              # ...avoid duplicate lines if called twice

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)       # ...and each handler filters for itself
    console.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console)
    logger.addHandler(file_handler)
    return logger


if __name__ == "__main__":
    log = setup_logging()
    log.debug("Only in the file")
    log.info("On screen AND in the file")
```

**Key points**
- Logger level and handler level both apply. A message must pass both.
- Handlers let one message go to several destinations at different detail levels.
- `RotatingFileHandler` stops a log file from filling the disk. `TimedRotatingFileHandler` rotates by time (daily, for example).
- Clearing handlers (or checking `if not logger.handlers`) prevents the "every line is printed twice" bug.

---

## Exercise 8 solution (capstone)

```python
import csv
import logging
import sys
from logging.handlers import RotatingFileHandler

VALID_STATUSES = {"PAID", "PENDING", "FAILED"}


class ValidationError(Exception):
    """A single row failed validation."""


def setup_logging(log_file="orders.log"):
    logger = logging.getLogger("orders")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s")

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)

    fh = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    logger.addHandler(console)
    logger.addHandler(fh)
    return logger


logger = setup_logging()


def validate_row(row):
    customer = (row.get("customer") or "").strip()
    if not customer:
        raise ValidationError("customer is missing")

    raw_amount = (row.get("amount") or "").replace(",", "").strip()
    try:
        amount = float(raw_amount)
    except ValueError:
        raise ValidationError(f"amount is not a number: {row.get('amount')!r}") from None
    if amount <= 0:
        raise ValidationError(f"amount must be positive: {amount}")

    status = (row.get("status") or "").strip().upper()
    if status not in VALID_STATUSES:
        raise ValidationError(f"invalid status: {row.get('status')!r}")

    return {
        "order_id": row.get("order_id"),
        "customer": customer,
        "amount": amount,
        "status": status,
    }


def process_file(path):
    valid, invalid = [], 0
    with open(path, newline="", encoding="utf-8-sig") as f:
        # Line 1 is the header, so data starts at line 2
        for line_no, row in enumerate(csv.DictReader(f), start=2):
            try:
                valid.append(validate_row(row))
                logger.debug("Line %d OK: %s", line_no, row)
            except ValidationError as e:
                invalid += 1
                logger.warning("Line %d skipped: %s", line_no, e)
    return valid, invalid


def main(path):
    logger.info("Starting processing of %s", path)
    try:
        valid, invalid = process_file(path)
    except FileNotFoundError:
        logger.error("Input file not found: %s", path)
        return 2
    except Exception:
        logger.exception("Unexpected failure while processing %s", path)
        return 3

    total = sum(r["amount"] for r in valid)
    logger.info("Done: %d valid, %d invalid, total amount = %.2f", len(valid), invalid, total)
    return 1 if invalid else 0


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "orders.csv"
    sys.exit(main(path))
```

**Expected result with the sample file:** 2 valid orders (1001 and 1005) plus 1007 (status `failed` is accepted case-insensitively), so 3 valid and 4 invalid. Exit code `1`.

**Key points**
- **Two layers of exceptions:** `ValidationError` is expected and handled per row. Unexpected errors fall to the outer `except Exception`, which logs a traceback and returns a distinct exit code.
- **Line numbers in warnings** make it quick for a support person to find the bad row in the source file.
- **`from None`** hides the unhelpful inner `ValueError` since we raise a clearer message.
- **`utf-8-sig`** handles the invisible BOM that Excel adds.
- **Exit codes** let a scheduler distinguish "fine", "partial", "input missing", and "crashed".
- If a header is misspelled (say `custmer`), every row fails with "customer is missing". That's a useful lesson: when *every* row fails, it's usually a format problem, not bad data. A real solution would check the header up front and fail fast.

---

## Exercise 9 solution

1. **Error type and message:** `KeyError: 'amount'`. A dictionary didn't have an `"amount"` key.
2. **Where:** `billing.py`, function `calculate_total`, line 12.
3. **Your code that started the chain:** `main.py` line 35 calls `calculate_total(orders)`. The traceback reads top to bottom as the call chain, and the *last* frame is where it blew up.
4. **Likely cause:** at least one order dictionary in `orders` is missing the `amount` key, probably bad or incomplete upstream data.
5. **Improvements:**
   - Validate the records before summing (or use `o.get("amount")` and handle `None` deliberately).
   - Log which order failed, e.g. its ID, so you don't have to guess.
   - Log the count of records received and rejected, to spot data problems early.
   - Don't silently default missing amounts to 0, because that hides bad data and produces wrong totals.

---

## Exercise 10 notes

- **F8** steps over a line, and **F7** steps into a function call.
- The **Variables** panel shows live values. Look at `row` and `e` when they change.
- **Evaluate Expression** (Alt+F8) lets you run any expression in the paused context.
- A **conditional breakpoint** (right-click the red dot) saves you from stepping through thousands of good rows to reach the one bad one. This is exactly how you'd debug a specific failing record.

---

# Self-check questions

Answer these out loud or in writing, as you would in an interview.

1. Why is `except Exception: pass` dangerous in a batch job?
2. What's the difference between `logger.error(e)` and `logger.exception("msg")`?
3. A script logs at INFO in production, but you need DEBUG details for one incident. What are your options?
4. Why do both loggers and handlers have levels?
5. What does `raise ... from e` add, compared to just raising a new exception?
6. When should a script stop completely on error, and when should it skip and continue?
7. Why use a non-zero exit code even when you've already logged the error?

**Model answers**
1. It hides real failures: data is lost or wrong and nobody is alerted. Failures should be logged at minimum, and ideally cause a non-zero exit code.
2. `error(e)` logs only the message. `exception("msg")` logs your message plus the full traceback.
3. Change the log level through configuration or an environment variable and restart or reload. Better still, have the level configurable without code changes. Avoid leaving DEBUG on permanently, because of volume and sensitive data.
4. The logger decides what's captured at all, and each handler decides what goes to its destination. That's how the console can show INFO while the file keeps DEBUG.
5. It preserves the original exception as the cause, so you see the full chain, and gives callers a cleaner, domain-specific exception type.
6. Stop when continuing could cause damage or wrong output (corrupt config, can't connect to the database, bad header). Skip and continue when failures are isolated and recoverable (one bad row), as long as you record what was skipped.
7. Logs are for humans. Exit codes are for machines. Schedulers and alerting depend on them to know the job failed.
