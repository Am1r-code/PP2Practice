# config.py
# Database connection configuration.
# Edit the values below to match your PostgreSQL setup,
# or set the corresponding environment variables.

import os

DB_CONFIG = {
    "host":     os.getenv("PB_HOST",     "localhost"),
    "port":     int(os.getenv("PB_PORT", "5432")),
    "dbname":   os.getenv("PB_DBNAME",   "phonebook"),
    "user":     os.getenv("PB_USER",     "postgres"),
    "password": os.getenv("PB_PASSWORD", ""),
}

# Pagination default
PAGE_SIZE = 10
