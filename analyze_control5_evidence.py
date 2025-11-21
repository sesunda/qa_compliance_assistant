import psycopg2

conn = psycopg2.connect('postgresql://qcaadmin:admin123@psql-qca-dev-2f37g0.postgres.database.azure.com/qca_db')
cur = conn.cursor()

# Get evidence details for Control 5
cur.execute('''
    SELECT id, title, evidence_type, verification_status, description, uploaded_at
    FROM evidence 
    WHERE control_id = 5 
    ORDER BY uploaded_at
''')
rows = cur.fetchall()

print("=== Evidence for Control 5 (MFA) ===\n")
for i, row in enumerate(rows, 1):
    print(f"{i}. Evidence ID: {row[0]}")
    print(f"   Title: {row[1]}")
    print(f"   Type: {row[2]}")
    print(f"   Verification Status: {row[3]}")
    print(f"   Description: {row[4]}")
    print(f"   Uploaded: {row[5]}")
    print()

# Calculate quality score manually
evidence_types = {}
verified_count = 0
total_count = len(rows)

for row in rows:
    evidence_type = row[2]
    verification_status = row[3]
    
    if evidence_type:
        evidence_types[evidence_type] = evidence_types.get(evidence_type, 0) + 1
    
    if verification_status == 'approved':
        verified_count += 1

print(f"\n=== Quality Score Calculation ===")
print(f"Total Evidence: {total_count}")
print(f"Unique Types: {list(evidence_types.keys())}")
print(f"Type Count: {len(evidence_types)}")
print(f"Verified (approved): {verified_count}")
print(f"Pending: {total_count - verified_count}")

# Calculate score components
type_diversity_score = min(len(evidence_types) / 4.0, 1.0) if total_count > 0 else 0
verification_score = verified_count / total_count if total_count > 0 else 0
quantity_score = min(total_count / 3.0, 1.0) if total_count > 0 else 0

quality_score = (type_diversity_score * 0.4 + verification_score * 0.4 + quantity_score * 0.2) * 100

print(f"\nType Diversity Score: {type_diversity_score:.2f} (40% weight)")
print(f"Verification Score: {verification_score:.2f} (40% weight)")
print(f"Quantity Score: {quantity_score:.2f} (20% weight)")
print(f"\nFinal Quality Score: {quality_score:.1f}%")

# Identify missing evidence types
expected_types = ['policy_document', 'audit_report', 'configuration_screenshot', 'test_result']
missing_types = [t for t in expected_types if t not in evidence_types]

print(f"\n=== Gaps Identified ===")
if missing_types:
    print(f"Missing Evidence Types: {', '.join(missing_types)}")
if total_count - verified_count > 0:
    print(f"Pending Verification: {total_count - verified_count} evidence items")

print(f"\n=== To Reach 80% Score ===")
print("You need:")
print("1. Type Diversity: 3-4 different evidence types (policy, audit, config, test)")
print("2. Verification: Get all evidence approved")
print("3. Quantity: At least 3 evidence items total")

cur.close()
conn.close()
