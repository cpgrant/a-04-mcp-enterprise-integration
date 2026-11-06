"""Shared read-only PostgreSQL connection for AI-A04."""

import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


def get_connection():
    """Connect using the restricted enterprise reader account."""

    password = os.getenv("POSTGRES_READ_PASSWORD")

    if not password:
        raise RuntimeError(
            "POSTGRES_READ_PASSWORD is not configured"
        )

    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=int(os.getenv("POSTGRES_PORT", "55432")),
        dbname=os.getenv("POSTGRES_DB", "a04_enterprise"),
        user="a04_reader",
        password=password,
        row_factory=dict_row,
        connect_timeout=5,
        options="-c default_transaction_read_only=on "
                "-c statement_timeout=5000",
    )
