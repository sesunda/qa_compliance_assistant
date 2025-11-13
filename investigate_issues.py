#!/usr/bin/env python3
"""Comprehensive investigation of all issues"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

# Database connection - Azure
DB_HOST = "psql-qca-dev-2f37g0.postgres.database.azure.com"
DB_USER = "qcaadmin"
DB_PASSWORD = "admin123"
DB_NAME = "qca_db"

print("=" * 100)
print("COMPREHENSIVE ISSUE INVESTIGATION")
print("=" * 100)

try:
    print("\nConnecting to Azure database...")
    conn = psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        sslmode="require",
        cursor_factory=RealDictCursor
    )
    cursor = conn.cursor()
    print("✓ Connected successfully\n")

    # ============================================================================
    # ISSUE 3: Check if Evidence #39 exists
    # ============================================================================
    print("=" * 100)
    print("ISSUE 3: EVIDENCE #39 INVESTIGATION")
    print("=" * 100)
    
    cursor.execute("""
        SELECT 
            e.id,
            e.control_id,
            e.title,
            e.description,
            e.file_path,
            e.evidence_type,
            e.verification_status,
            e.submitted_by,
            e.reviewed_by,
            e.created_at,
            e.updated_at,
            c.name as control_name,
            u.username as submitted_by_username,
            u.full_name as submitted_by_name,
            u.agency_id as user_agency_id,
            a.name as agency_name
        FROM evidence e
        LEFT JOIN controls c ON e.control_id = c.id
        LEFT JOIN users u ON e.submitted_by = u.id
        LEFT JOIN agencies a ON u.agency_id = a.id
        WHERE e.id = 39
    """)
    
    evidence_39 = cursor.fetchone()
    
    if evidence_39:
        print("\n✓ EVIDENCE #39 EXISTS IN DATABASE\n")
        print(f"ID: {evidence_39['id']}")
        print(f"Control ID: {evidence_39['control_id']} ({evidence_39['control_name']})")
        print(f"Title: {evidence_39['title']}")
        print(f"Description: {evidence_39['description']}")
        print(f"File Path: {evidence_39['file_path']}")
        print(f"Evidence Type: {evidence_39['evidence_type']}")
        print(f"Status: {evidence_39['verification_status']}")
        print(f"Submitted By: {evidence_39['submitted_by_name']} ({evidence_39['submitted_by_username']})")
        print(f"Agency: {evidence_39['agency_name']} (ID: {evidence_39['user_agency_id']})")
        print(f"Created: {evidence_39['created_at']}")
        print(f"Updated: {evidence_39['updated_at']}")
    else:
        print("\n❌ EVIDENCE #39 NOT FOUND IN DATABASE!")
        print("This means the upload failed at the database level.")
    
    # Check all evidence for Alice
    print("\n" + "-" * 100)
    print("ALL EVIDENCE SUBMITTED BY ALICE (User ID: 2)")
    print("-" * 100)
    
    cursor.execute("""
        SELECT 
            e.id,
            e.control_id,
            e.title,
            e.verification_status,
            e.created_at,
            c.name as control_name,
            u.agency_id
        FROM evidence e
        LEFT JOIN controls c ON e.control_id = c.id
        LEFT JOIN users u ON e.submitted_by = u.id
        WHERE e.submitted_by = 2
        ORDER BY e.created_at DESC
    """)
    
    alice_evidence = cursor.fetchall()
    
    if alice_evidence:
        print(f"\n✓ Found {len(alice_evidence)} evidence record(s) from Alice:\n")
        for ev in alice_evidence:
            print(f"  Evidence #{ev['id']}: {ev['title']}")
            print(f"    Control: {ev['control_name']} (ID: {ev['control_id']})")
            print(f"    Status: {ev['verification_status']}")
            print(f"    Agency ID: {ev['agency_id']}")
            print(f"    Created: {ev['created_at']}")
            print()
    else:
        print("\n❌ NO EVIDENCE FOUND FROM ALICE!")
        print("This confirms the uploads are not reaching the database.")
    
    # Check total evidence in system
    print("-" * 100)
    print("TOTAL EVIDENCE IN SYSTEM (All Users)")
    print("-" * 100)
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN verification_status = 'pending' THEN 1 END) as pending,
            COUNT(CASE WHEN verification_status = 'under_review' THEN 1 END) as under_review,
            COUNT(CASE WHEN verification_status = 'approved' THEN 1 END) as approved,
            COUNT(CASE WHEN verification_status = 'rejected' THEN 1 END) as rejected
        FROM evidence
    """)
    
    total_evidence = cursor.fetchone()
    print(f"\nTotal Evidence: {total_evidence['total']}")
    print(f"  Pending: {total_evidence['pending']}")
    print(f"  Under Review: {total_evidence['under_review']}")
    print(f"  Approved: {total_evidence['approved']}")
    print(f"  Rejected: {total_evidence['rejected']}")

    # ============================================================================
    # ISSUE 4: Check Agent Tasks
    # ============================================================================
    print("\n" + "=" * 100)
    print("ISSUE 4: AGENT TASKS INVESTIGATION")
    print("=" * 100)
    
    cursor.execute("""
        SELECT 
            at.id,
            at.task_type,
            at.status,
            at.result,
            at.error_message,
            at.created_at,
            at.started_at,
            at.completed_at,
            u.username,
            u.full_name
        FROM agent_tasks at
        LEFT JOIN users u ON at.created_by = u.id
        WHERE u.id = 2
        ORDER BY at.created_at DESC
        LIMIT 10
    """)
    
    agent_tasks = cursor.fetchall()
    
    if agent_tasks:
        print(f"\n✓ Found {len(agent_tasks)} agent task(s) for Alice\n")
        
        failed_count = 0
        for task in agent_tasks:
            status_emoji = {
                'pending': '⏳',
                'running': '🔄',
                'completed': '✅',
                'failed': '❌',
                'cancelled': '🚫'
            }.get(task['status'], '❓')
            
            print(f"{status_emoji} Task #{task['id']}: {task['task_type']}")
            print(f"   Status: {task['status']}")
            print(f"   Created: {task['created_at']}")
            
            if task['started_at']:
                print(f"   Started: {task['started_at']}")
            if task['completed_at']:
                print(f"   Completed: {task['completed_at']}")
            
            if task['status'] == 'failed':
                failed_count += 1
                print(f"   ❌ Error: {task['error_message']}")
                if task['result']:
                    result = task['result'] if isinstance(task['result'], dict) else {}
                    print(f"   Result: {json.dumps(result, indent=6)}")
            
            print()
        
        print(f"Failed Tasks: {failed_count}")
    else:
        print("\n❌ NO AGENT TASKS FOUND FOR ALICE")
    
    # Check MCP-related errors
    print("-" * 100)
    print("MCP ERROR ANALYSIS")
    print("-" * 100)
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_mcp_errors,
            error_message
        FROM agent_tasks
        WHERE error_message LIKE '%MCP%' OR error_message LIKE '%Name or service not known%'
        GROUP BY error_message
    """)
    
    mcp_errors = cursor.fetchall()
    
    if mcp_errors:
        print(f"\n✓ Found {len(mcp_errors)} type(s) of MCP errors:\n")
        for err in mcp_errors:
            print(f"  Count: {err['total_mcp_errors']}")
            print(f"  Error: {err['error_message']}")
            print()
    else:
        print("\n✓ No MCP-related errors found")

    # ============================================================================
    # CHECK DATABASE SCHEMA & CONSTRAINTS
    # ============================================================================
    print("\n" + "=" * 100)
    print("DATABASE SCHEMA CHECK")
    print("=" * 100)
    
    # Check if evidence table has proper columns
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'evidence'
        ORDER BY ordinal_position
    """)
    
    evidence_columns = cursor.fetchall()
    
    print("\nEvidence Table Schema:")
    print("-" * 100)
    for col in evidence_columns:
        nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
        print(f"  {col['column_name']:30} {col['data_type']:20} {nullable}")
    
    # Check file type constraints
    cursor.execute("""
        SELECT 
            conname as constraint_name,
            pg_get_constraintdef(oid) as constraint_definition
        FROM pg_constraint
        WHERE conrelid = 'evidence'::regclass
    """)
    
    constraints = cursor.fetchall()
    
    if constraints:
        print("\nEvidence Table Constraints:")
        print("-" * 100)
        for const in constraints:
            print(f"  {const['constraint_name']}: {const['constraint_definition']}")

    # ============================================================================
    # CHECK TIMEZONE SETTINGS
    # ============================================================================
    print("\n" + "=" * 100)
    print("ISSUE 1: TIMEZONE INVESTIGATION")
    print("=" * 100)
    
    cursor.execute("SHOW timezone;")
    db_timezone = cursor.fetchone()
    print(f"\nDatabase Timezone: {db_timezone['TimeZone']}")
    
    cursor.execute("SELECT NOW(), NOW() AT TIME ZONE 'UTC', NOW() AT TIME ZONE 'Asia/Singapore';")
    times = cursor.fetchone()
    print(f"Current DB Time: {times['now']}")
    print(f"UTC Time: {times['timezone']}")
    print(f"Singapore Time: {times['timezone_1']}")
    
    # Check timestamps in evidence table
    cursor.execute("""
        SELECT 
            created_at,
            created_at AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Singapore' as created_at_sgt
        FROM evidence
        ORDER BY created_at DESC
        LIMIT 5
    """)
    
    recent_evidence = cursor.fetchall()
    
    if recent_evidence:
        print("\nRecent Evidence Timestamps:")
        print("-" * 100)
        for ev in recent_evidence:
            print(f"  DB: {ev['created_at']} → SGT: {ev['created_at_sgt']}")

    # ============================================================================
    # CHECK ALICE'S PERMISSIONS
    # ============================================================================
    print("\n" + "=" * 100)
    print("ALICE'S PERMISSIONS CHECK")
    print("=" * 100)
    
    cursor.execute("""
        SELECT 
            u.id,
            u.username,
            u.full_name,
            u.email,
            u.is_active,
            u.agency_id,
            a.name as agency_name,
            ur.name as role_name,
            ur.permissions
        FROM users u
        LEFT JOIN agencies a ON u.agency_id = a.id
        LEFT JOIN user_roles ur ON u.role_id = ur.id
        WHERE u.username = 'alice'
    """)
    
    alice = cursor.fetchone()
    
    if alice:
        print(f"\nAlice's Profile:")
        print(f"  User ID: {alice['id']}")
        print(f"  Username: {alice['username']}")
        print(f"  Full Name: {alice['full_name']}")
        print(f"  Email: {alice['email']}")
        print(f"  Role: {alice['role_name']}")
        print(f"  Agency: {alice['agency_name']} (ID: {alice['agency_id']})")
        print(f"  Active: {alice['is_active']}")
        print(f"  Permissions: {json.dumps(alice['permissions'], indent=2)}")

    # ============================================================================
    # CHECK CONTROLS ALICE HAS ACCESS TO
    # ============================================================================
    print("\n" + "=" * 100)
    print("CONTROLS IN ALICE'S PROJECTS")
    print("=" * 100)
    
    cursor.execute("""
        SELECT 
            c.id,
            c.name,
            c.description,
            p.id as project_id,
            p.name as project_name,
            p.agency_id
        FROM controls c
        LEFT JOIN projects p ON c.project_id = p.id
        WHERE p.agency_id = %s OR p.agency_id IS NULL
        ORDER BY c.id
        LIMIT 10
    """, (alice['agency_id'],))
    
    controls = cursor.fetchall()
    
    if controls:
        print(f"\n✓ Found {len(controls)} control(s) accessible to Alice:\n")
        for ctrl in controls:
            print(f"  Control #{ctrl['id']}: {ctrl['name']}")
            print(f"    Project: {ctrl['project_name']} (ID: {ctrl['project_id']})")
            print(f"    Agency ID: {ctrl['agency_id']}")
            print()

    # ============================================================================
    # ISSUE 2: CHECK FILE UPLOAD CONFIGURATION
    # ============================================================================
    print("\n" + "=" * 100)
    print("ISSUE 2: FILE UPLOAD CONFIGURATION")
    print("=" * 100)
    
    print("\nThis requires checking:")
    print("  1. API endpoint file type validation")
    print("  2. Frontend file input accept attribute")
    print("  3. Backend MIME type checking")
    print("  4. Evidence type enum values")
    print("\n(Will check code files separately)")

    # ============================================================================
    # SUMMARY
    # ============================================================================
    print("\n" + "=" * 100)
    print("INVESTIGATION SUMMARY")
    print("=" * 100)
    
    print("\n✓ Database Connection: Working")
    print(f"✓ Alice's User Record: Found (ID: {alice['id']})")
    print(f"✓ Alice's Agency: {alice['agency_name']} (ID: {alice['agency_id']})")
    print(f"✓ Alice's Role: {alice['role_name']}")
    
    if evidence_39:
        print(f"✓ Evidence #39: EXISTS")
    else:
        print(f"❌ Evidence #39: NOT FOUND")
    
    print(f"✓ Total Evidence from Alice: {len(alice_evidence) if alice_evidence else 0}")
    print(f"✓ Total Agent Tasks: {len(agent_tasks) if agent_tasks else 0}")
    print(f"✓ Failed Agent Tasks: {failed_count if agent_tasks else 0}")
    print(f"✓ Database Timezone: {db_timezone['TimeZone']}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 100)
    print("✅ INVESTIGATION COMPLETE")
    print("=" * 100)

except psycopg2.Error as e:
    print(f"\n❌ Database error: {e}")
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
