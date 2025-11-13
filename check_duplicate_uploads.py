import psycopg2
from datetime import datetime

conn = psycopg2.connect(
    host='psql-qca-dev-2f37g0.postgres.database.azure.com',
    database='qca_db',
    user='admin',
    password='admin123',
    sslmode='require'
)
cur = conn.cursor()

# Check recent evidence uploads
cur.execute('''
    SELECT id, control_id, title, original_filename, verification_status, 
           uploaded_by, created_at
    FROM evidence 
    WHERE uploaded_by = 2 
    ORDER BY created_at DESC 
    LIMIT 10
''')

print('Recent Evidence Records (Alice):')
print('=' * 100)
for row in cur.fetchall():
    print(f'ID: {row[0]}, Control: {row[1]}, Title: {row[2][:50]}, File: {row[3]}, Status: {row[4]}, Created: {row[6]}')

print('\n')

# Check recent agent tasks related to evidence upload
cur.execute('''
    SELECT id, task_type, status, result, created_at
    FROM agent_tasks 
    WHERE created_by = 2 
    AND task_type = 'request_evidence_upload'
    ORDER BY created_at DESC 
    LIMIT 10
''')

print('Recent Evidence Upload Tasks (Alice):')
print('=' * 100)
for row in cur.fetchall():
    result_preview = str(row[3])[:200] if row[3] else 'None'
    print(f'ID: {row[0]}, Type: {row[1]}, Status: {row[2]}, Created: {row[4]}')
    print(f'  Result: {result_preview}')
    print()

cur.close()
conn.close()
