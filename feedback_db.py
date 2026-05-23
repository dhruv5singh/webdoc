import sqlite3
import pandas as pd
from datetime import datetime

FEEDBACK_DB_PATH = "feedback.db"


def get_connection():
    return sqlite3.connect(FEEDBACK_DB_PATH, check_same_thread=False)


def init_feedback_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bug_reports (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email       TEXT,
            name        TEXT,
            title       TEXT NOT NULL,
            description TEXT NOT NULL,
            steps       TEXT,
            severity    TEXT,
            timestamp   TEXT NOT NULL,
            status      TEXT DEFAULT 'Pending'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feature_requests (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            email       TEXT,
            name        TEXT,
            title       TEXT NOT NULL,
            description TEXT NOT NULL,
            use_case    TEXT,
            priority    TEXT,
            timestamp   TEXT NOT NULL,
            status      TEXT DEFAULT 'Pending'
        )
    """)

    # Check if 'status' column exists in bug_reports (for schema migration of existing databases)
    cursor.execute("PRAGMA table_info(bug_reports)")
    columns = [col[1] for col in cursor.fetchall()]
    if "status" not in columns:
        cursor.execute("ALTER TABLE bug_reports ADD COLUMN status TEXT DEFAULT 'Pending'")

    # Check if 'status' column exists in feature_requests
    cursor.execute("PRAGMA table_info(feature_requests)")
    columns = [col[1] for col in cursor.fetchall()]
    if "status" not in columns:
        cursor.execute("ALTER TABLE feature_requests ADD COLUMN status TEXT DEFAULT 'Pending'")

    conn.commit()
    conn.close()


def insert_bug_report(email: str, name: str, title: str,
                      description: str, steps: str, severity: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO bug_reports
            (email, name, title, description, steps, severity, timestamp, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')
        """,
        (email, name, title, description, steps, severity,
         datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def insert_feature_request(email: str, name: str, title: str,
                           description: str, use_case: str, priority: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO feature_requests
            (email, name, title, description, use_case, priority, timestamp, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')
        """,
        (email, name, title, description, use_case, priority,
         datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_bug_reports():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM bug_reports ORDER BY timestamp DESC", conn)
    conn.close()
    return df


def get_feature_requests():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM feature_requests ORDER BY timestamp DESC", conn)
    conn.close()
    return df


def update_bug_status(report_id: int, status: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE bug_reports SET status = ? WHERE id = ?",
        (status, report_id)
    )
    conn.commit()
    conn.close()


def update_feature_status(request_id: int, status: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE feature_requests SET status = ? WHERE id = ?",
        (status, request_id)
    )
    conn.commit()
    conn.close()


def delete_bug_report(report_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bug_reports WHERE id = ?", (report_id,))
    conn.commit()
    conn.close()


def delete_feature_request(request_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM feature_requests WHERE id = ?", (request_id,))
    conn.commit()
    conn.close()

