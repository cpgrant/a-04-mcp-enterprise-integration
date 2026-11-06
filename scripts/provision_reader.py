"""Provision the read-only database role for AI-A04."""

import os

import psycopg
from psycopg import sql
from dotenv import load_dotenv

load_dotenv()

ROLE = "a04_reader"
SCHEMAS = ("crm", "erp", "finance")

password = os.environ["POSTGRES_READ_PASSWORD"]

connection = {
    "host": "127.0.0.1",
    "port": 55432,
    "dbname": os.environ["POSTGRES_DB"],
    "user": os.environ["POSTGRES_USER"],
    "password": os.environ["POSTGRES_PASSWORD"],
}

with psycopg.connect(**connection, autocommit=True) as conn:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM pg_roles WHERE rolname = %s",
            (ROLE,),
        )

        if cur.fetchone() is None:
            cur.execute(
                sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(
                    sql.Identifier(ROLE),
                    sql.Literal(password),
                )
            )
            print("Created database reader role")
        else:
            cur.execute(
                sql.SQL("ALTER ROLE {} PASSWORD {}").format(
                    sql.Identifier(ROLE),
                    sql.Literal(password),
                )
            )
            print("Updated existing reader credentials")

        cur.execute(
            sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                sql.Identifier(connection["dbname"]),
                sql.Identifier(ROLE),
            )
        )

        for schema in SCHEMAS:
            cur.execute(
                sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                    sql.Identifier(schema),
                    sql.Identifier(ROLE),
                )
            )

            cur.execute(
                sql.SQL(
                    "GRANT SELECT ON ALL TABLES IN SCHEMA {} TO {}"
                ).format(
                    sql.Identifier(schema),
                    sql.Identifier(ROLE),
                )
            )

            cur.execute(
                sql.SQL(
                    "ALTER DEFAULT PRIVILEGES IN SCHEMA {} "
                    "GRANT SELECT ON TABLES TO {}"
                ).format(
                    sql.Identifier(schema),
                    sql.Identifier(ROLE),
                )
            )

print("Reader provisioned for CRM, ERP and Finance")
