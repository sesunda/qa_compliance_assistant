"""
RAG (Retrieval-Augmented Generation) API endpoints
Provides backfill and search operations for evidence and controls
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from ..database import get_db
from ..rag.evidence_indexer import EvidenceIndexer
from ..rag.control_indexer import ControlIndexer

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])
logger = logging.getLogger(__name__)

@router.post("/backfill")
async def backfill_all(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Backfill all existing evidence and controls to Azure Search
    """
    try:
        logger.info("🔄 Starting backfill for evidence and controls...")
        
        # Backfill evidence
        evidence_indexer = EvidenceIndexer()
        evidence_result = await evidence_indexer.backfill_evidence(db)
        
        # Backfill controls
        control_indexer = ControlIndexer()
        control_result = await control_indexer.backfill_controls(db)
        
        result = {
            "success": True,
            "evidence": evidence_result,
            "controls": control_result,
            "total_indexed": evidence_result.get("indexed", 0) + control_result.get("indexed", 0),
            "total_items": evidence_result.get("total", 0) + control_result.get("total", 0)
        }
        
        logger.info(f"✅ Backfill complete: {result['total_indexed']}/{result['total_items']} items indexed")
        return result
        
    except Exception as e:
        logger.error(f"❌ Backfill failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Backfill failed: {str(e)}")


@router.post("/backfill/evidence")
async def backfill_evidence_only(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Backfill only evidence to Azure Search
    """
    try:
        logger.info("🔄 Starting backfill for evidence...")
        
        evidence_indexer = EvidenceIndexer()
        result = await evidence_indexer.backfill_evidence(db)
        
        logger.info(f"✅ Evidence backfill complete: {result.get('indexed', 0)}/{result.get('total', 0)} indexed")
        return result
        
    except Exception as e:
        logger.error(f"❌ Evidence backfill failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evidence backfill failed: {str(e)}")


@router.post("/backfill/controls")
async def backfill_controls_only(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Backfill only controls to Azure Search
    """
    try:
        logger.info("🔄 Starting backfill for controls...")
        
        control_indexer = ControlIndexer()
        result = await control_indexer.backfill_controls(db)
        
        logger.info(f"✅ Control backfill complete: {result.get('indexed', 0)}/{result.get('total', 0)} indexed")
        return result
        
    except Exception as e:
        logger.error(f"❌ Control backfill failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Control backfill failed: {str(e)}")


@router.get("/health")
async def rag_health() -> Dict[str, Any]:
    """
    Check RAG system health
    """
    try:
        # Test that indexers can be instantiated
        evidence_indexer = EvidenceIndexer()
        control_indexer = ControlIndexer()
        
        return {
            "status": "healthy",
            "evidence_indexer": "ready",
            "control_indexer": "ready"
        }
    except Exception as e:
        logger.error(f"❌ RAG health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e)
        }
