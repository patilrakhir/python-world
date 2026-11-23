# Workbook 2: Log Parsing and Text Processing

Level: intermediate. Scenario: you're on the production support team and your job is to turn raw logs into answers. *What broke? When? How badly? Who is affected?*

**Skills practised:** reading files line by line, regular expressions, `Counter`, `defaultdict`, generators, simple statistics, and writing a report.

**How to use:** Read Part 1 and attempt each exercise in PyCharm. Look at Part 2 (solutions) only after you've tried.

---

## Setup

1. Put `generate_sample_data.py` in your PyCharm project folder and run it once. It creates a `sample_data/` folder.
2. Files used in this workbook:
   - `sample_data/app.log` is the main application log (about 3,000 lines, with a few junk lines).
   - `sample_data/logs/` has three per-service logs that share transaction IDs.
3. Look at the data first. Open `app.log` in PyCharm and spend two minutes reading it. You'll see these line types:

```
2026-11-10 00:00:45,758 INFO  [api-gw] GET /orders/693 200 took=145ms
2026-11-10 00:01:30,429 WARN  [auth-svc] Failed login for user=meera ip=192.168.1.32
2026-11-10 02:14:07,331 ERROR [payment-svc] txn=88412 Timeout connecting to db-prod-02
2026-11-10 03:05:11,002 INFO  [order-svc] Job 217 completed
---- stack trace truncated ----
```

Note the junk line. Real logs always have some, and your code must not crash on it.

---

# Part 1: Exercises

### Exercise 1: Count lines by level
Write `count_levels(path)` that returns how many lines there are for each level (INFO, WARN, ERROR) and how many lines could not be parsed.

**Think about:** What data structure makes counting easy? How do you keep memory usage tiny?

### Exercise 2: Build a reusable parser
Write a regex (compiled once) and a generator function `parse_log(path)` that yields one dictionary per valid line with the keys `ts`, `level`, `service`, `message`. Malformed lines should be skipped. Test it by printing the first 5 records.

**Think about:** Why a generator instead of returning a list?

### Exercise 3: Top 5 error messages
The same error appears with different transaction numbers (`txn=88412`, `txn=70211`). Find the **5 most frequent error messages**, treating those as the same error. Print each with its count.

**Hint:** Normalise the message before counting, for example by replacing digits with a placeholder.

### Exercise 4: Errors per hour
Count ERROR lines per hour and print a simple text bar chart, for example:

```
2026-11-10 02 | ###### 6
2026-11-10 03 | ## 2
```

Which hour is the worst? Can you spot the spike that was injected into the data?

### Exercise 5: Response time analysis
The `api-gw` lines look like `GET /orders/693 200 took=145ms`. Calculate:
- Total requests, average response time, maximum, and the 95th percentile (p95).
- The 5 slowest requests, with timestamps.
- The percentage of requests that returned a 5xx status.

**Think about:** Why is p95 more useful than the average for support work?

### Exercise 6: Trace one transaction across services
In `sample_data/logs/` you have three service logs. Write `trace(txn_id, folder)` that gathers every line for one transaction across all three files, sorts them by time, and prints the gap since the previous step. Report the slowest hop.

Test with `88412`. It must **not** also pick up lines for `884120`, which exists in the data on purpose.

### Exercise 7: Suspicious login attempts
From the `Failed login for user=... ip=...` lines, find IP addresses with more than 50 failed attempts, and for each show how many *different* usernames were tried. Why does the number of distinct usernames matter?

### Exercise 8: A generator pipeline and "tail"
Build small chained generators: `read_lines → parse → filter`, so you can write something like "give me the first 5 ERROR lines from `payment-svc`" without loading the whole file. Then implement a `tail(path, n)` that returns the last `n` lines of a file using constant memory.

### Exercise 9 (Capstone): Daily log summary report
Write a command-line script `log_report.py` that takes a log file path and writes a `report.txt` containing:
1. Total lines, parsed lines, and skipped lines.
2. Counts per level.
3. Errors per service.
4. Top 5 error messages (normalised).
5. The peak error hour.
6. Response time stats (count, average, p95, max) and the number of slow requests (1000 ms or more).
7. Suspicious IPs (more than 50 failures).

Make it a single pass over the file. Return exit code `1` if there are more than 100 errors, otherwise `0`.

---

# Part 2: Solutions

All solutions assume you run them from the project folder where `sample_data/` lives.

## Shared building blocks

```python
import re

LOG_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3}\s+"
    r"(?P<level>[A-Z]+)\s+\[(?P<service>[^\]]+)\]\s+(?P<message>.*)$"
)
```

Why this works:
- `^` and `$` anchor the match to the whole line.
- Named groups (`?P<name>`) let you write `m["level"]` instead of remembering group numbers.
- `\s+` copes with `INFO ` and `ERROR` having different padding.
- `[^\]]+` means "anything except a closing bracket", which captures the service name.

---

## Exercise 1 solution

```python
from collections import Counter

LOG_PATH = "sample_data/app.log"


def count_levels(path):
    counts, skipped = Counter(), 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:                       # streams: one line in memory at a time
            m = LOG_RE.match(line)
            if m:
                counts[m["level"]] += 1
            else:
                skipped += 1
    return counts, skipped


if __name__ == "__main__":
    counts, skipped = count_levels(LOG_PATH)
    print(dict(counts), "skipped:", skipped)
```

**Key points**
- `Counter` is a dict that starts every count at zero.
- `for line in f` streams the file, so a 5 GB log works the same as a 5 KB one.
- `errors="replace"` stops one bad byte from crashing the run.
- Counting skipped lines tells you how clean the data is.

---

## Exercise 2 solution

```python
def parse_log(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = LOG_RE.match(line)
            if m:
                yield m.groupdict()


if __name__ == "__main__":
    from itertools import islice
    for record in islice(parse_log(LOG_PATH), 5):
        print(record)
```

**Key points**
- A generator (`yield`) produces one record at a time. A list of 5 million records could exhaust memory, but a generator never holds more than one.
- `islice` takes the first N items from any generator without consuming the rest.
- `groupdict()` returns a plain dictionary of the named groups.

---

## Exercise 3 solution

```python
import re
from collections import Counter

NUM_RE = re.compile(r"\d+")


def top_error_messages(path, n=5):
    counter = Counter()
    for rec in parse_log(path):
        if rec["level"] == "ERROR":
            normalised = NUM_RE.sub("<N>", rec["message"])   # txn=88412 -> txn=<N>
            counter[normalised] += 1
    return counter.most_common(n)


if __name__ == "__main__":
    for msg, count in top_error_messages(LOG_PATH):
        print(f"{count:5d}  {msg}")
```

**Key points**
- Normalising (replace IDs, numbers, timestamps with placeholders) groups the *same kind* of error together. This is the core of log analysis.
- Be careful about over-normalising. `db-prod-02` becomes `db-prod-<N>`, which is fine here, but could merge distinct servers in other logs.
- `most_common(n)` gives the top results already sorted.

---

## Exercise 4 solution

```python
from collections import Counter


def errors_per_hour(path):
    per_hour = Counter()
    for rec in parse_log(path):
        if rec["level"] == "ERROR":
            per_hour[rec["ts"][:13]] += 1      # "2026-11-10 02:14:07" -> "2026-11-10 02"
    return per_hour


if __name__ == "__main__":
    per_hour = errors_per_hour(LOG_PATH)
    for hour, count in sorted(per_hour.items()):
        print(f"{hour} | {'#' * (count // 2)} {count}")
    worst_hour, worst_count = per_hour.most_common(1)[0]
    print("Worst hour:", worst_hour, "with", worst_count, "errors")
```

**Key points**
- Slicing the timestamp string is a quick way to bucket by hour without parsing dates (it works because the format is fixed-width).
- A text bar chart is a fast way to see a spike. You'll find the worst hour is the one with the injected `payment-svc` timeouts.
- For other bucket sizes (5 minutes), you'd parse to `datetime` and round down the minutes.

---

## Exercise 5 solution

```python
import re

REQ_RE = re.compile(r"(?P<method>[A-Z]+) (?P<path>\S+) (?P<status>\d{3}) took=(?P<ms>\d+)ms")


def response_stats(path):
    times, slowest, errors_5xx = [], [], 0
    for rec in parse_log(path):
        m = REQ_RE.search(rec["message"])
        if not m:
            continue
        ms = int(m["ms"])
        times.append(ms)
        slowest.append((ms, rec["ts"], m["method"], m["path"]))
        if m["status"].startswith("5"):
            errors_5xx += 1

    if not times:
        return None
    times_sorted = sorted(times)
    p95 = times_sorted[int(0.95 * (len(times_sorted) - 1))]
    return {
        "count": len(times),
        "average": sum(times) / len(times),
        "max": times_sorted[-1],
        "p95": p95,
        "slowest5": sorted(slowest, reverse=True)[:5],
        "pct_5xx": 100 * errors_5xx / len(times),
    }


if __name__ == "__main__":
    stats = response_stats(LOG_PATH)
    print(f"Requests: {stats['count']}  avg: {stats['average']:.0f}ms  "
          f"p95: {stats['p95']}ms  max: {stats['max']}ms  5xx: {stats['pct_5xx']:.1f}%")
    for ms, ts, method, p in stats["slowest5"]:
        print(f"  {ms:5d}ms  {ts}  {method} {p}")
```

**Key points**
- **p95 vs average:** a few very slow requests barely move the average, but p95 tells you "95% of users get a response within this time", which is closer to the real user experience.
- `search` (not `match`) because the request text sits in the *middle* of the line.
- Always guard against empty data before dividing.

---

## Exercise 6 solution

```python
import re
from datetime import datetime
from pathlib import Path

TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})")


def trace(txn_id, folder="sample_data/logs"):
    pattern = re.compile(rf"\btxn={re.escape(txn_id)}\b")   # \b stops 88412 matching 884120
    hits = []
    for log_file in Path(folder).glob("*.log"):
        with open(log_file, encoding="utf-8", errors="replace") as f:
            for line in f:
                if pattern.search(line):
                    m = TS_RE.match(line)
                    if m:
                        ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S,%f")
                        hits.append((ts, line.rstrip()))
    hits.sort(key=lambda h: h[0])
    return hits


def print_trace(hits):
    if not hits:
        print("No entries found")
        return
    prev, slowest = None, (0.0, "")
    for ts, line in hits:
        gap = (ts - prev).total_seconds() if prev else 0.0
        print(f"+{gap:6.2f}s  {line}")
        if gap > slowest[0]:
            slowest = (gap, line)
        prev = ts
    print(f"\nSlowest hop: {slowest[0]:.2f}s  before: {slowest[1]}")


if __name__ == "__main__":
    print_trace(trace("88412"))
```

**Key points**
- `\b` (word boundary) prevents a partial match. Without it you'd silently include another transaction's lines. This is a classic production bug.
- Sort by parsed `datetime`, not by the text.
- `re.escape` makes the pattern safe even if the ID has special characters.
- In real systems, clocks on different servers can drift, so gaps across hosts need to be read with caution.

---

## Exercise 7 solution

```python
import re
from collections import Counter, defaultdict

LOGIN_RE = re.compile(r"Failed login for user=(?P<user>\S+) ip=(?P<ip>\S+)")


def suspicious_ips(path, threshold=50):
    attempts = Counter()
    users = defaultdict(set)
    for rec in parse_log(path):
        m = LOGIN_RE.search(rec["message"])
        if m:
            attempts[m["ip"]] += 1
            users[m["ip"]].add(m["user"])
    return [(ip, n, len(users[ip])) for ip, n in attempts.most_common() if n > threshold]


if __name__ == "__main__":
    for ip, n, distinct in suspicious_ips(LOG_PATH):
        print(f"{ip:15} failures={n:4d} distinct_users={distinct}")
```

**Key points**
- `defaultdict(set)` creates an empty set automatically for a new key, and a set keeps usernames unique.
- **Why distinct users matter:** one IP failing repeatedly on *one* user often means a forgotten password. One IP trying *many* usernames suggests an automated attack (credential stuffing or brute force). Different situation, different response.

---

## Exercise 8 solution

```python
from collections import deque
from itertools import islice


def read_lines(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            yield line.rstrip("\n")


def parse(lines):
    for line in lines:
        m = LOG_RE.match(line)
        if m:
            yield m.groupdict()


def only(records, **conditions):
    for r in records:
        if all(r[key] == value for key, value in conditions.items()):
            yield r


def tail(path, n=10):
    return list(deque(read_lines(path), maxlen=n))   # keeps only the last n lines


if __name__ == "__main__":
    pipeline = only(parse(read_lines(LOG_PATH)), level="ERROR", service="payment-svc")
    for rec in islice(pipeline, 5):
        print(rec["ts"], rec["message"])
    print("--- last 3 lines ---")
    for line in tail(LOG_PATH, 3):
        print(line)
```

**Key points**
- Each stage is lazy. Nothing is read until you ask for results, and `islice` stops the pipeline after 5 matches, so the rest of the file is never read.
- `deque(maxlen=n)` automatically discards old items, giving you a constant-memory tail.
- Small composable functions are easy to test and reuse.

---

## Exercise 9 solution (capstone)

```python
#!/usr/bin/env python3
import argparse
import re
import sys
from collections import Counter

LOG_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3}\s+"
    r"(?P<level>[A-Z]+)\s+\[(?P<service>[^\]]+)\]\s+(?P<message>.*)$"
)
REQ_RE = re.compile(r"(?P<method>[A-Z]+) (?P<path>\S+) (?P<status>\d{3}) took=(?P<ms>\d+)ms")
LOGIN_RE = re.compile(r"Failed login for user=(?P<user>\S+) ip=(?P<ip>\S+)")
NUM_RE = re.compile(r"\d+")

SLOW_MS = 1000
ERROR_LIMIT = 100


def analyse(path):
    s = {
        "total": 0, "skipped": 0,
        "levels": Counter(), "errors_by_service": Counter(),
        "error_messages": Counter(), "errors_by_hour": Counter(),
        "failed_logins": Counter(), "times": [], "slow": 0,
    }
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:                         # single pass over the file
            s["total"] += 1
            m = LOG_RE.match(line)
            if not m:
                s["skipped"] += 1
                continue
            level, svc, msg, ts = m["level"], m["service"], m["message"], m["ts"]
            s["levels"][level] += 1

            if level == "ERROR":
                s["errors_by_service"][svc] += 1
                s["error_messages"][NUM_RE.sub("<N>", msg)] += 1
                s["errors_by_hour"][ts[:13]] += 1

            req = REQ_RE.search(msg)
            if req:
                ms = int(req["ms"])
                s["times"].append(ms)
                if ms >= SLOW_MS:
                    s["slow"] += 1

            login = LOGIN_RE.search(msg)
            if login:
                s["failed_logins"][login["ip"]] += 1
    return s


def render(s, source):
    out = [f"LOG SUMMARY REPORT for {source}", "=" * 50]
    out.append(f"Lines: {s['total']}  parsed: {s['total'] - s['skipped']}  skipped: {s['skipped']}")
    out.append("")
    out.append("Counts by level:")
    for level, n in s["levels"].most_common():
        out.append(f"  {level:<6}{n}")
    out.append("")
    out.append("Errors by service:")
    for svc, n in s["errors_by_service"].most_common():
        out.append(f"  {svc:<15}{n}")
    out.append("")
    out.append("Top 5 error messages:")
    for msg, n in s["error_messages"].most_common(5):
        out.append(f"  {n:5d}  {msg}")
    if s["errors_by_hour"]:
        hour, n = s["errors_by_hour"].most_common(1)[0]
        out.append("")
        out.append(f"Peak error hour: {hour}:00 with {n} errors")
    out.append("")
    t = sorted(s["times"])
    if t:
        p95 = t[int(0.95 * (len(t) - 1))]
        out.append(f"Response times: n={len(t)} avg={sum(t)/len(t):.0f}ms "
                   f"p95={p95}ms max={t[-1]}ms slow(>={SLOW_MS}ms)={s['slow']}")
    out.append("")
    out.append("Suspicious IPs (more than 50 failed logins):")
    flagged = [(ip, n) for ip, n in s["failed_logins"].most_common() if n > 50]
    out.extend(f"  {ip:15}{n}" for ip, n in flagged) if flagged else out.append("  none")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Summarise an application log")
    ap.add_argument("logfile")
    ap.add_argument("--output", default="report.txt")
    args = ap.parse_args(argv)

    try:
        stats = analyse(args.logfile)
    except FileNotFoundError:
        print(f"File not found: {args.logfile}", file=sys.stderr)
        return 2

    report = render(stats, args.logfile)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report + "\n")
    print(report)
    return 1 if stats["levels"]["ERROR"] > ERROR_LIMIT else 0


if __name__ == "__main__":
    sys.exit(main())
```

Run it in PyCharm with *Parameters:* `sample_data/app.log`. With the sample data you should see an error peak in the 13:00 hour, two suspicious IPs (`10.0.0.5` and `10.0.0.9`), and exit code `1`, because there are far more than 100 errors.

**Key points**
- **One pass, many metrics.** Each line is read once and feeds several counters, which is far faster than re-reading the file per question.
- **Separate "analyse" from "render".** Analysis returns data and rendering formats it, so you can later output JSON or send an email without touching the logic.
- **Exit code** tells a scheduler whether the day looked bad.
- Handles a missing file with a clear message and a distinct exit code.

---

# Self-check questions

1. Why read a log with `for line in f` instead of `f.readlines()`?
2. What does `\b` do in a regex, and why did the transaction tracer need it?
3. Why normalise error messages before counting them?
4. Why is p95 often more useful than the average for response times?
5. What is the advantage of generators in a log-processing pipeline?
6. A single IP has 500 failed logins for one username, and another has 40 failed logins across 35 different usernames. Which looks more suspicious, and why?
7. Your script reports "0 errors" for a log that you know contains errors. List three things you'd check.

**Model answers**
1. It streams one line at a time, so memory use stays small regardless of file size. `readlines()` loads everything into memory and can crash on large files.
2. It matches a word boundary, so the pattern for `txn=88412` doesn't also match `txn=884120`. Without it, you'd mix another transaction's lines into your trace.
3. The same underlying error carries different IDs and numbers. Without normalising, every line looks unique and you can't see which problem is most common.
4. A few extreme values barely move the average, while p95 shows what the slowest 5% experience, which better reflects real user pain and SLA risk.
5. They process data lazily, one item at a time, so you can chain filters and stop early without loading or scanning the whole file.
6. The 40 failures across 35 usernames is more suspicious, since it looks like automated guessing across accounts. 500 failures on one username may just be a locked-out user or a misconfigured service retrying an old password, though it still deserves a look.
7. Whether the regex actually matches the real log format (case, spacing, timestamp format), whether you're reading the right file or an already-rotated one, whether the skipped-lines count is huge (a parsing problem), and whether the level text is `ERROR` or something like `Error` or `SEVERE`.
