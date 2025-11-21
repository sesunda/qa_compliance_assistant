import psycopg2

# Database connection
conn = psycopg2.connect(
    host='psql-qca-dev-2f37g0.postgres.database.azure.com',
    database='qca_db',
    user='qcaadmin',
    password='admin123',
    port=5432,
    sslmode='require'
)
cur = conn.cursor()

print("=== All Users in Database ===")
cur.execute("""
    SELECT id, username, email, agency_id, role_id
    FROM users
    ORDER BY id
""")
users = cur.fetchall()
print(f"Total users: {len(users)}\n")
for user in users:
    print(f"ID: {user[0]:3} | Username: {user[1]:20} | Email: {user[2]:30} | Agency: {user[3]} | Role: {user[4]}")

print("\n=== All Agencies ===")
cur.execute("SELECT id, name FROM agencies ORDER BY id")
agencies = cur.fetchall()
for agency in agencies:
    print(f"Agency ID {agency[0]}: {agency[1]}")

conn.close()
