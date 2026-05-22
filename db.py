import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = "user_data.db"


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            website TEXT,
            ip_address TEXT,
            reachability_status TEXT,
            http_status TEXT,
            final_status TEXT,
            avg_response REAL,
            load_time REAL,
            packet_loss REAL,
            dns_time REAL,
            ssl_days_left INTEGER,
            category TEXT,
            alert TEXT,
            diagnosis TEXT
        )
        """
    )

    conn.commit()
    conn.close()



def insert_record(email: str, data: dict):
    if not data:
        return

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO records (
            email,
            timestamp,
            website,
            ip_address,
            reachability_status,
            http_status,
            final_status,
            avg_response,
            load_time,
            packet_loss,
            dns_time,
            ssl_days_left,
            category,
            alert,
            diagnosis
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            email,
            data.get("Timestamp").isoformat() if isinstance(data.get("Timestamp"), datetime) else data.get("Timestamp"),
            data.get("Website"),
            data.get("IP Address"),
            data.get("Reachability Status"),
            data.get("HTTP Status"),
            data.get("Final Status"),
            data.get("Avg Response Time (ms)"),
            data.get("Load Time (ms)"),
            data.get("Packet Loss %"),
            data.get("DNS Time (ms)"),
            data.get("SSL Days Left"),
            data.get("Category"),
            data.get("Alert"),
            data.get("Diagnosis"),
        ),
    )

    conn.commit()
    conn.close()



def get_history(email: str):
    conn = get_connection()

    query = """
    SELECT * FROM records
    WHERE email = ?
    ORDER BY timestamp DESC
    """

    df = pd.read_sql_query(query, conn, params=(email,))

    conn.close()

    return df



def get_website_history(email: str, website: str):
    conn = get_connection()

    query = """
    SELECT * FROM records
    WHERE email = ? AND website LIKE ?
    ORDER BY timestamp ASC
    """

    df = pd.read_sql_query(query, conn, params=(email, f"%{website}%"))

    conn.close()

    return df
