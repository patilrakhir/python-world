#!/usr/bin/env python3
"""
generate_sample_data.py

Creates realistic, slightly messy sample data for the practice workbooks.
Run it ONCE from your PyCharm project folder:

    python generate_sample_data.py

It creates a folder called  sample_data/  containing:
    app.log                 - 3000+ lines of mixed application logs (with some junk lines)
    logs/                   - per-service logs sharing transaction IDs (for tracing)
    old_logs/               - log files of different ages (for archive/cleanup practice)
    orders.csv              - messy order export (mixed formats, duplicates, bad values)
    orders.json             - the "other system's" version of the same orders (with differences)
    support.db              - SQLite database: customers, orders, jobs

Re-running it recreates everything with the same random seed, so results are repeatable.
"""
import csv
import json
import os
import random
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)
OUT = Path("sample_data")

SERVICES = ["payment-svc", "auth-svc", "order-svc", "inventory-svc", "api-gw"]
ERROR_MESSAGES = [
    "Timeout connecting to db-prod-02",
    "Connection refused by payment-gateway",
    "NullPointerException in OrderMapper",
    "Disk usage above 90% on /var/log",
    "Failed to parse response from inventory API",
]
CUSTOMERS = [
    ("Asha Patil", "Pune"), ("Ravi Kumar", "Mumbai"), ("Meera Shah", "Ahmedabad"),
    ("John Mathew", "Kochi"), ("Priya Nair", "Chennai"), ("Karan Singh", "Delhi"),
    ("Sneha Joshi", "Nashik"), ("Amit Deshmukh", "Sangamner"),
]
STATUSES = ["PAID", "PENDING", "FAILED", "REFUNDED"]


# --------------------------------------------------------------------------- logs
def fmt(ts, level, svc, msg):
    return f"{ts:%Y-%m-%d %H:%M:%S},{random.randint(0, 999):03d} {level:<5} [{svc}] {msg}"


def make_app_log(path, n=3000):
    ts = datetime(2026, 11, 10, 0, 0, 0)
    lines = []
    bad_ips = ["10.0.0.5", "10.0.0.9"]
    normal_ips = [f"192.168.1.{i}" for i in range(10, 40)]
    for i in range(n):
        if i % 250 == 0:
            lines.append("---- stack trace truncated ----")  # junk line
        if 1500 <= i < 1540:  # an error spike on payment-svc
            ts += timedelta(seconds=random.randint(2, 8))
            lines.append(fmt(ts, "ERROR", "payment-svc",
                             f"txn={random.randint(10000, 99999)} Timeout connecting to db-prod-02"))
            continue
        ts += timedelta(seconds=random.randint(5, 60))
        r = random.random()
        if r < 0.55:
            ms = random.randint(20, 400) if random.random() < 0.93 else random.randint(1500, 6000)
            status = 200 if random.random() < 0.95 else 500
            method = random.choice(["GET", "GET", "GET", "POST"])
            lines.append(fmt(ts, "INFO", "api-gw",
                             f"{method} /orders/{random.randint(1, 999)} {status} took={ms}ms"))
        elif r < 0.70:
            ip = random.choice(bad_ips) if random.random() < 0.5 else random.choice(normal_ips)
            user = random.choice(["admin", "root", "asha", "ravi", "meera"])
            lines.append(fmt(ts, "WARN", "auth-svc", f"Failed login for user={user} ip={ip}"))
        elif r < 0.85:
            svc = random.choice(SERVICES)
            lines.append(fmt(ts, "ERROR", svc,
                             f"txn={random.randint(10000, 99999)} {random.choice(ERROR_MESSAGES)}"))
        else:
            svc = random.choice(SERVICES)
            lines.append(fmt(ts, "INFO", svc, f"Job {random.randint(1, 500)} completed"))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_trace_logs(folder, n_txn=60):
    folder.mkdir(parents=True, exist_ok=True)
    steps = [
        ("order-svc", "Order received"),
        ("payment-svc", "Payment initiated"),
        ("inventory-svc", "Stock reserved"),
        ("payment-svc", "Payment completed"),
        ("order-svc", "Order confirmed"),
    ]
    entries = []
    base = datetime(2026, 11, 10, 9, 0, 0)
    for k in range(n_txn):
        txn = 88400 + k
        t = base + timedelta(seconds=k * 20)
        slow_step = random.randint(1, 4) if random.random() < 0.2 else None
        for idx, (svc, msg) in enumerate(steps):
            gap = random.uniform(4, 9) if slow_step == idx else random.uniform(0.05, 0.6)
            t += timedelta(seconds=gap)
            line = f"{t:%Y-%m-%d %H:%M:%S},{t.microsecond // 1000:03d} INFO  [{svc}] txn={txn} {msg}"
            entries.append((t, svc, line))
    # a similar-looking ID, to catch sloppy matching (txn=88412 must NOT match txn=884120)
    t = base + timedelta(seconds=5)
    entries.append((t, "order-svc",
                    f"{t:%Y-%m-%d %H:%M:%S},000 INFO  [order-svc] txn=884120 Order received"))
    entries.sort(key=lambda e: e[0])
    per_service = {}
    for _, svc, line in entries:
        per_service.setdefault(svc, []).append(line)
    for svc, lines in per_service.items():
        (folder / f"{svc}.log").write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_old_logs(folder):
    folder.mkdir(parents=True, exist_ok=True)
    now = time.time()
    for days in [1, 2, 3, 8, 10, 15, 20, 30, 45]:
        stamp = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        p = folder / f"app-{stamp}.log"
        p.write_text("2026-11-01 10:00:00,000 INFO  [api-gw] sample line\n" * 2000, encoding="utf-8")
        mtime = now - days * 86400
        os.utime(p, (mtime, mtime))
    (folder / "app-current.log").write_text("2026-11-18 10:00:00,000 INFO  [api-gw] live line\n",
                                            encoding="utf-8")


# ------------------------------------------------------------------------- orders
def make_orders(out):
    start = datetime(2026, 11, 1)
    base = []
    for i in range(200):
        name, city = random.choice(CUSTOMERS)
        base.append({
            "order_id": str(1001 + i),
            "customer": name,
            "city": city,
            "amount": round(random.uniform(50, 5000), 2),
            "status": random.choice(STATUSES),
            "order_date": (start + timedelta(days=random.randint(0, 9))).date(),
        })

    # ---- messy CSV
    def messy_date(d):
        return random.choice([d.isoformat(), d.strftime("%d/%m/%Y"), d.strftime("%d-%b-%Y")])

    def messy_amount(a):
        r = random.random()
        if r < 0.20:
            return f"{a:,.2f}"          # e.g. 1,234.50 (csv module will quote it)
        if r < 0.30:
            return f" {a} "
        if r < 0.33:
            return "N/A"
        return str(a)

    def messy_status(s):
        return random.choice([s, s.lower(), f" {s} ", s.title()])

    rows = []
    for o in base:
        rows.append({
            "order_id": o["order_id"],
            "customer": "" if random.random() < 0.02 else o["customer"],
            "amount": messy_amount(o["amount"]),
            "status": messy_status(o["status"]),
            "order_date": messy_date(o["order_date"]),
        })
    rows.extend(random.sample(rows, 6))  # duplicates

    with open(out / "orders.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["order_id", "customer", "amount", "status", "order_date"])
        w.writeheader()
        w.writerows(rows)

    # ---- the other system's JSON (nested customer, with deliberate differences)
    other = [dict(o) for o in base]
    drop = {o["order_id"] for o in random.sample(other, 5)}
    other = [o for o in other if o["order_id"] not in drop]
    for o in random.sample(other, 4):
        o["amount"] = round(o["amount"] + 10, 2)
    for o in random.sample(other, 3):
        o["status"] = random.choice([s for s in STATUSES if s != o["status"]])
    for k in range(3):
        name, city = random.choice(CUSTOMERS)
        other.append({"order_id": str(2001 + k), "customer": name, "city": city,
                      "amount": round(random.uniform(50, 500), 2), "status": "PAID",
                      "order_date": datetime(2026, 11, 10).date()})
    payload = [{
        "order_id": o["order_id"],
        "customer": {"name": o["customer"], "city": o["city"]},
        "amount": o["amount"],
        "status": o["status"],
        "order_date": o["order_date"].isoformat(),
    } for o in other]
    (out / "orders.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------- database
def make_db(path):
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL, city TEXT);
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            amount REAL NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE jobs (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            started_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)
    conn.executemany("INSERT INTO customers (id, name, city) VALUES (?, ?, ?)",
                     [(i + 1, n, c) for i, (n, c) in enumerate(CUSTOMERS)])
    now = datetime.now().replace(microsecond=0)
    orders = []
    for i in range(300):
        cust = 99 if i % 60 == 0 else random.randint(1, len(CUSTOMERS))  # 99 = orphan customer
        created = now - timedelta(hours=random.randint(1, 240))
        orders.append((cust, round(random.uniform(50, 5000), 2), random.choice(STATUSES),
                       created.isoformat()))
    conn.executemany("INSERT INTO orders (customer_id, amount, status, created_at) VALUES (?, ?, ?, ?)",
                     orders)

    names = ["nightly-report", "invoice-sync", "stock-refresh", "email-digest"]
    jobs = []
    for _ in range(30):  # healthy history
        started = now - timedelta(hours=random.randint(2, 48))
        jobs.append((random.choice(names), "DONE", started, started + timedelta(minutes=random.randint(1, 20))))
    for minutes in (45, 95, 400):  # stuck jobs
        started = now - timedelta(minutes=minutes)
        jobs.append((random.choice(names), "RUNNING", started, started + timedelta(minutes=1)))
    for minutes in (5, 12):  # healthy running jobs
        started = now - timedelta(minutes=minutes)
        jobs.append((random.choice(names), "RUNNING", started, now))
    for hours in (3, 9, 20, 22, 23, 23, 23):  # recent failures
        started = now - timedelta(hours=hours)
        jobs.append((random.choice(names), "FAILED", started, started + timedelta(minutes=2)))
    conn.executemany(
        "INSERT INTO jobs (name, status, started_at, updated_at) VALUES (?, ?, ?, ?)",
        [(n, s, a.isoformat(timespec="seconds"), b.isoformat(timespec="seconds")) for n, s, a, b in jobs])
    conn.commit()
    conn.close()


def main():
    OUT.mkdir(exist_ok=True)
    make_app_log(OUT / "app.log")
    make_trace_logs(OUT / "logs")
    make_old_logs(OUT / "old_logs")
    make_orders(OUT)
    make_db(OUT / "support.db")
    print("Sample data created in:", OUT.resolve())
    for p in sorted(OUT.rglob("*")):
        if p.is_file():
            print(f"  {p.relative_to(OUT)}  ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
