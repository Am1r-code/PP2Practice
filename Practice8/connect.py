"""
connect.py
----------
Provides a single helper function that opens and returns a psycopg2
connection using the settings in config.py.
"""

import psycopg2
from config import DB_CONFIG


def get_connection():
    """Return a new psycopg2 connection, or raise on failure."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.OperationalError as e:
        print(f"[ERROR] Could not connect to the database: {e}")
        raise
