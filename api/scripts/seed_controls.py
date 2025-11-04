"""
Seed IM8 Framework Controls into the controls table

This script creates control instances from the control_catalog for a project.
Run as a module from the project root:
    docker exec qca_api python -m api.scripts.seed_controls
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from api.src.database import SessionLocal
from api.src.models import Control, ControlCatalog

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_controls(project_id: int = 1, agency_id: int = 1):
    """
    Seed controls from control_catalog into controls table for a project
    
    Args:
        project_id: Project ID to create controls for
        agency_id: Agency ID for the controls
    """
    db = SessionLocal()
    try:
        # Get all controls from catalog
        catalog_controls = db.query(ControlCatalog).all()
        
        logger.info(f"Found {len(catalog_controls)} controls in catalog")
        
        created_count = 0
        skipped_count = 0
        
        for catalog_control in catalog_controls:
            # Check if control already exists for this project
            existing = db.query(Control).filter(
                Control.project_id == project_id,
                Control.name == catalog_control.title
            ).first()
            
            if existing:
                logger.info(f"Skipping existing control: {catalog_control.title}")
                skipped_count += 1
                continue
            
            # Create new control instance
            control = Control(
                project_id=project_id,
                agency_id=agency_id,
                name=catalog_control.title,
                description=catalog_control.description or "",
                control_type=catalog_control.family or "security",
                status="active"
            )
            
            db.add(control)
            created_count += 1
            logger.info(f"Created control: {catalog_control.title}")
        
        db.commit()
        
        logger.info(f"✅ Seeding complete! Created {created_count} controls, skipped {skipped_count}")
        
        # Display final count
        total = db.query(Control).filter(Control.project_id == project_id).count()
        logger.info(f"Total controls for project {project_id}: {total}")
        
    except Exception as e:
        logger.error(f"Error seeding controls: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    seed_controls(project_id=1, agency_id=1)
