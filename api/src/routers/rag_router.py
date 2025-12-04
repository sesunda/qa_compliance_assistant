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
        
        logger.info(f"✅ Controls backfill complete: {result.get('indexed', 0)}/{result.get('total', 0)} indexed")
        return result
        
    except Exception as e:
        logger.error(f"❌ Controls backfill failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Controls backfill failed: {str(e)}")


@router.post("/reindex/evidence/{evidence_id}")
async def reindex_evidence_by_id(evidence_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Reindex a specific evidence by ID (useful for manual fixes)
    """
    try:
        from ..models import Evidence
        from ..services.evidence_storage import evidence_storage_service
        import os
        import tempfile
        
        logger.info(f"🔄 Reindexing evidence {evidence_id}...")
        
        # Get evidence from database
        evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
        if not evidence:
            raise HTTPException(status_code=404, detail=f"Evidence {evidence_id} not found")
        
        if not evidence.file_path:
            raise HTTPException(status_code=400, detail=f"Evidence {evidence_id} has no file_path")
        
        # Download file content from storage (works for both local and Azure)
        try:
            file_content = evidence_storage_service.download_file(evidence.file_path)
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))
        
        # Write to temporary file for processing
        _, file_ext = os.path.splitext(evidence.file_path)
        with tempfile.NamedTemporaryFile(mode='wb', suffix=file_ext, delete=False) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            # Build metadata
            evidence_metadata = {
                "control_id": evidence.control_id,
                "project_id": getattr(evidence, 'project_id', None),
                "agency_id": evidence.agency_id,
                "title": evidence.title,
                "file_name": evidence.original_filename or os.path.basename(evidence.file_path),
                "evidence_type": evidence.evidence_type
            }
            
            # Index it
            evidence_indexer = EvidenceIndexer()
            result = await evidence_indexer.index_evidence(
                evidence_id=evidence.id,
                file_path=temp_file_path,
                evidence_metadata=evidence_metadata,
                db=db
            )
            
            logger.info(f"✅ Reindexed evidence {evidence_id}")
            return result
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete temp file {temp_file_path}: {e}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Reindex failed for evidence {evidence_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Reindex failed: {str(e)}")


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
