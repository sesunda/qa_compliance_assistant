import psycopg2

# Database connection
conn = psycopg2.connect(
    'postgresql://qcaadmin:admin123@psql-qca-dev-2f37g0.postgres.database.azure.com:5432/qca_db?sslmode=require'
)
cur = conn.cursor()

print("Current migration state:")
cur.execute("SELECT * FROM alembic_version")
print(cur.fetchall())

print("\nUpdating to version 0000053 (trigger already exists)...")
cur.execute("UPDATE alembic_version SET version_num = '0000053'")
conn.commit()

print("New migration state:")
cur.execute("SELECT * FROM alembic_version")
print(cur.fetchall())

conn.close()
print("\n✅ Migration state updated!")
