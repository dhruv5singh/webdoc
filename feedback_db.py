import sqlite3
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
            timestamp   TEXT NOT NULL
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
            timestamp   TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def insert_bug_report(email: str, name: str, title: str,
                      description: str, steps: str, severity: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO bug_reports
            (email, name, title, description, steps, severity, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
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
            (email, name, title, description, use_case, priority, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (email, name, title, description, use_case, priority,
         datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
