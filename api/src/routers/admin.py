from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from ..database import get_db
from ..models import Evidence
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

@router.post("/fix-evidence-path/{evidence_id}")
async def fix_evidence_path(
    evidence_id: int,
    correct_path: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Admin endpoint to fix evidence file_path in database
    """
    try:
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            raise HTTPException(status_code=404, detail=f"Evidence {evidence_id} not found")
        
        old_path = evidence.file_path
        evidence.file_path = correct_path
        db.commit()
        db.refresh(evidence)
        
        logger.info(f"✅ Fixed Evidence {evidence_id} path: {old_path} → {correct_path}")
        
        return {
            "evidence_id": evidence_id,
            "old_path": old_path,
            "new_path": correct_path,
            "status": "fixed"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to fix evidence path: {e}")
        raise HTTPException(status_code=500, detail=str(e))
