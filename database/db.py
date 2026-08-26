import os
import sqlite3
from datetime import date, timedelta

from werkzeug.security import generate_password_hash

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_BASE_DIR)
DB_PATH = os.path.join(_PROJECT_ROOT, "expense_tracker.db")

_CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
)
"""

_CREATE_EXPENSES_TABLE = """
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    date TEXT NOT NULL,
    description TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id)
)
"""


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    try:
        conn.execute(_CREATE_USERS_TABLE)
        conn.execute(_CREATE_EXPENSES_TABLE)
        conn.commit()
    finally:
        conn.close()


def seed_db():
    conn = get_db()
    try:
        row = conn.execute("SELECT COUNT(*) FROM users").fetchone()
        if row[0] > 0:
            return

        password_hash = generate_password_hash("demo123")
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", password_hash),
        )
        user_id = cur.lastrowid

        first_of_month = date.today().replace(day=1)

        def d(offset_days):
            return (first_of_month + timedelta(days=offset_days)).strftime("%Y-%m-%d")

        expenses = [
            (user_id, 42.50, "Food", d(1), "Groceries run"),
            (user_id, 18.00, "Transport", d(4), "Bus fare top-up"),
            (user_id, 95.00, "Bills", d(8), "Electricity bill"),
            (user_id, 30.25, "Health", d(11), "Pharmacy"),
            (user_id, 22.99, "Entertainment", d(15), "Movie night"),
            (user_id, 64.10, "Shopping", d(18), "New shoes"),
            (user_id, 12.00, "Other", d(22), "Misc supplies"),
            (user_id, 27.80, "Food", d(25), "Restaurant dinner"),
        ]
        conn.executemany(
            """INSERT INTO expenses (user_id, amount, category, date, description)
               VALUES (?, ?, ?, ?, ?)""",
            expenses,
        )
        conn.commit()
    finally:
        conn.close()
