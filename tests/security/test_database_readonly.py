"""Verify PostgreSQL read-only enforcement for AI-A04."""

import psycopg
import pytest
from psycopg import sql

from src.adapters.db import get_connection


SCHEMAS = ("crm", "erp", "finance")


def enterprise_tables(conn):
    """Discover business tables without assuming table names."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT n.nspname, c.relname
            FROM pg_class AS c
            JOIN pg_namespace AS n
              ON n.oid = c.relnamespace
            WHERE n.nspname = ANY(%s)
              AND c.relkind IN ('r', 'p')
            ORDER BY n.nspname, c.relname
            """,
            (list(SCHEMAS),),
        )
        return cur.fetchall()


def test_reader_can_select_enterprise_tables():
    with get_connection() as conn:
        tables = enterprise_tables(conn)

        assert tables, "No enterprise tables discovered"
        assert {row["nspname"] for row in tables} == set(SCHEMAS)

        for table in tables:
            with conn.cursor() as cur:
                cur.execute(
                    sql.SQL("SELECT 1 FROM {}.{} LIMIT 1").format(
                        sql.Identifier(table["nspname"]),
                        sql.Identifier(table["relname"]),
                    )
                )
                cur.fetchall()


def test_reader_has_no_write_privileges():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    n.nspname,
                    c.relname,
                    has_table_privilege(
                        current_user, c.oid, 'INSERT'
                    ) AS can_insert,
                    has_table_privilege(
                        current_user, c.oid, 'UPDATE'
                    ) AS can_update,
                    has_table_privilege(
                        current_user, c.oid, 'DELETE'
                    ) AS can_delete,
                    has_table_privilege(
                        current_user, c.oid, 'TRUNCATE'
                    ) AS can_truncate
                FROM pg_class AS c
                JOIN pg_namespace AS n
                  ON n.oid = c.relnamespace
                WHERE n.nspname = ANY(%s)
                  AND c.relkind IN ('r', 'p')
                """,
                (list(SCHEMAS),),
            )
            rows = cur.fetchall()

        assert rows

        for row in rows:
            assert not row["can_insert"], row
            assert not row["can_update"], row
            assert not row["can_delete"], row
            assert not row["can_truncate"], row


def test_reader_cannot_delete_even_in_readwrite_transaction():
    with get_connection() as conn:
        table = enterprise_tables(conn)[0]

        conn.rollback()

        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            with conn.transaction():
                with conn.cursor() as cur:
                    # Test actual role privileges, not just the
                    # connection's default read-only setting.
                    cur.execute("SET TRANSACTION READ WRITE")

                    # WHERE FALSE ensures no data can match.
                    cur.execute(
                        sql.SQL(
                            "DELETE FROM {}.{} WHERE FALSE"
                        ).format(
                            sql.Identifier(table["nspname"]),
                            sql.Identifier(table["relname"]),
                        )
                    )
