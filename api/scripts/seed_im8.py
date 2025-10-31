"""Seed IM8 domain areas into the database.

Run as a module from the project root:
    python -m api.scripts.seed_im8

This script imports the project's DB session lazily to avoid import errors when
executing outside the package context in some editors or environments.
"""

from typing import List

from api.src.models import IM8DomainArea

areas = [
    {"code": "IM8-01", "name": "Access & Identity Management", "description": "User accounts, roles, privileged access."},
    {"code": "IM8-02", "name": "Network & Connectivity Security", "description": "Network segmentation, allow-by-exception."},
    {"code": "IM8-03", "name": "Application & Data Protection", "description": "Data classification, encryption, output sanitisation."},
    {"code": "IM8-04", "name": "Infrastructure & System Hardening", "description": "Patch management, least functionality, EOS assets."},
    {"code": "IM8-05", "name": "Secure Development & Supply Chain", "description": "Code repository controls, dependency pinning."},
    {"code": "IM8-06", "name": "Logging, Monitoring & Incident Response", "description": "Log aggregation, retention, alerting."},
    {"code": "IM8-07", "name": "Third-Party & Vendor Management", "description": "Outsourcing, supply-chain governance."},
    {"code": "IM8-08", "name": "Change, Release & Configuration Management", "description": "Change approvals, configuration drift control."},
    {"code": "IM8-09", "name": "Governance, Risk & Compliance (GRC)", "description": "Risk registers, SSPs, residual risk acceptance."},
    {"code": "IM8-10", "name": "Digital Service & Delivery Standards", "description": "DSS, agile delivery, lifecycle of digital services."},
]

def seed():
    # Import SessionLocal lazily so running this file directly or as a module works
    # even if the package import paths differ in the environment/editor.
    from api.src.database import SessionLocal

    db = SessionLocal()
    try:
        for a in areas:
            exists = db.query(IM8DomainArea).filter_by(code=a["code"]).first()
            if not exists:
                obj = IM8DomainArea(code=a["code"], name=a["name"], description=a["description"], framework_mappings={})
                db.add(obj)
        db.commit()
        print("Seeded IM8 knowledge areas")
    finally:
        db.close()

if __name__ == '__main__':
    seed()
