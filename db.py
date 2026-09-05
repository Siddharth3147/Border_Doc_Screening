"""
db.py

Very simple SQLite logging of past scans, so the officer using the
tool can see a history of recent checks - maps to the problem
statement's "Create a digital trail for investigations and
intelligence analysis" expected impact point.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join("scan_history", "scans.db")


def init_db():
    os.makedirs("scan_history", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            doc_type TEXT,
            final_score INTEGER,
            verdict TEXT
        )
    """)
    conn.commit()
    conn.close()


def log_scan(doc_type, final_score, verdict):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO scans (timestamp, doc_type, final_score, verdict) VALUES (?, ?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), doc_type, final_score, verdict)
    )
    conn.commit()
    conn.close()


def get_recent_scans(limit=10):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT timestamp, doc_type, final_score, verdict FROM scans ORDER BY id DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


if __name__ == "__main__":
    log_scan("Passport", 42, "MEDIUM RISK - Needs manual review")
    print(get_recent_scans())
