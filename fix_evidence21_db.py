#!/usr/bin/env python3
"""Fix Evidence 21 - set original_filename from file_path"""
import requests
import json

# API endpoint to run SQL via exec
api_url = "https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io"

# Run SQL update via container app exec
import subprocess

sql_command = """
UPDATE evidence 
SET original_filename = substring(file_path from '[^/\\\\]+$')
WHERE id = 21 AND original_filename IS NULL;
"""

print("Updating Evidence 21 original_filename...")
print(f"SQL: {sql_command}")

# Use Azure CLI to exec into container
result = subprocess.run([
    "az", "containerapp", "exec",
    "--name", "ca-api-qca-dev",
    "--resource-group", "rg-qca-dev",
    "--command", f"python -c \"from api.src.database import SessionLocal; from sqlalchemy import text; db = SessionLocal(); db.execute(text('{sql_command}')); db.commit(); print('Updated!'); db.close()\""
], capture_output=True, text=True)

print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("Return code:", result.returncode)
