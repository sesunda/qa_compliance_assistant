#!/usr/bin/env python3
"""Direct database reset - drops all tables and runs migration"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database connection from environment
DB_HOST = "psql-qca-dev-2f37g0.postgres.database.azure.com"
DB_USER = "qcaadmin"
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin123")
DB_NAME = "qca_db"

print("Connecting to database...")
conn = psycopg2.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    sslmode="require"
)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

cursor = conn.cursor()

print("Dropping all tables...")
cursor.execute("""
    DROP SCHEMA public CASCADE;
    CREATE SCHEMA public;
    GRANT ALL ON SCHEMA public TO qcaadmin;
    GRANT ALL ON SCHEMA public TO public;
""")

print("Database reset complete!")
print("Tables dropped. Alembic will create fresh schema on next container start.")

cursor.close()
conn.close()
