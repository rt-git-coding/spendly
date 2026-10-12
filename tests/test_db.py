import re
import sqlite3
from datetime import date

import pytest
from werkzeug.security import check_password_hash

from database import db

CATEGORIES = {"Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"}


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.init_db()
    connection = db.get_db()
    yield connection
    connection.close()


def columns(conn, table):
    return {row["name"]: row for row in conn.execute(f"PRAGMA table_info({table})")}


def test_schema_tables_and_columns(conn):
    tables = {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"users", "expenses"} <= tables

    users = columns(conn, "users")
    assert set(users) == {"id", "name", "email", "password_hash", "created_at"}
    for col in ("name", "email", "password_hash"):
        assert users[col]["notnull"] == 1

    expenses = columns(conn, "expenses")
    assert set(expenses) == {"id", "user_id", "amount", "category", "date", "description", "created_at"}
    for col in ("user_id", "amount", "category", "date"):
        assert expenses[col]["notnull"] == 1
    assert expenses["description"]["notnull"] == 0


def test_get_db_config(conn):
    assert conn.row_factory is sqlite3.Row
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_init_db_idempotent(conn):
    db.init_db()
    db.init_db()
    assert conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE name='users'").fetchone()[0] == 1


def test_seed_creates_demo_user_and_expenses(conn):
    db.seed_db()
    users = conn.execute("SELECT * FROM users").fetchall()
    assert len(users) == 1
    assert users[0]["email"] == "demo@spendly.com"
    assert users[0]["name"] == "Demo User"

    expenses = conn.execute("SELECT * FROM expenses").fetchall()
    assert len(expenses) == 8
    assert {e["user_id"] for e in expenses} == {users[0]["id"]}


def test_seed_idempotent(conn):
    db.seed_db()
    db.seed_db()
    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0] == 8


def test_password_is_hashed(conn):
    db.seed_db()
    stored = conn.execute("SELECT password_hash FROM users").fetchone()[0]
    assert stored != "demo123"
    assert check_password_hash(stored, "demo123")


def test_seed_covers_all_categories(conn):
    db.seed_db()
    found = {r[0] for r in conn.execute("SELECT DISTINCT category FROM expenses")}
    assert found == CATEGORIES


def test_seed_dates_in_current_month(conn):
    db.seed_db()
    prefix = date.today().strftime("%Y-%m")
    for (value,) in conn.execute("SELECT date FROM expenses"):
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)
        assert value.startswith(prefix)


def test_foreign_key_enforced(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)",
            (9999, 10.0, "Food", "2026-01-01"),
        )


def test_duplicate_email_rejected(conn):
    insert = "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)"
    conn.execute(insert, ("A", "a@example.com", "x"))
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(insert, ("B", "a@example.com", "y"))
