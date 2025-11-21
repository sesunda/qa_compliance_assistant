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

print("=== Checking Alice Tan's User Record ===")
cur.execute("""
    SELECT id, username, email, agency_id, role_id
    FROM users
    WHERE username = 'alice.tan'
""")
user = cur.fetchone()
if user:
    print(f"User ID: {user[0]}")
    print(f"Username: {user[1]}")
    print(f"Email: {user[2]}")
    print(f"Agency ID: {user[3]}")
    print(f"Role ID: {user[4]}")
else:
    print("❌ User 'alice.tan' not found!")
    conn.close()
    exit(1)

print("\n=== Available Agencies ===")
cur.execute("SELECT id, name FROM agencies ORDER BY id")
agencies = cur.fetchall()
for agency in agencies:
    print(f"Agency ID {agency[0]}: {agency[1]}")

if user[3] is None:
    print("\n⚠️  Alice Tan has no agency_id assigned!")
    if agencies:
        first_agency_id = agencies[0][0]
        print(f"\n🔧 Assigning agency_id = {first_agency_id} ({agencies[0][1]})")
        cur.execute("""
            UPDATE users 
            SET agency_id = %s 
            WHERE username = 'alice.tan'
        """, (first_agency_id,))
        conn.commit()
        print("✅ Agency ID updated successfully!")
        
        # Verify
        cur.execute("""
            SELECT u.id, u.username, u.agency_id, a.name as agency_name
            FROM users u
            LEFT JOIN agencies a ON u.agency_id = a.id
            WHERE u.username = 'alice.tan'
        """)
        updated_user = cur.fetchone()
        print(f"\n✅ Verified: {updated_user[1]} is now in agency '{updated_user[3]}' (ID: {updated_user[2]})")
    else:
        print("\n❌ No agencies found in database! Please create an agency first.")
else:
    print(f"\n✅ Alice Tan already has agency_id = {user[3]}")

conn.close()
print("\n✅ Script completed!")
