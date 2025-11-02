"""
Evidence auto-fetcher for retrieving files from various sources.

Supports:
- Local filesystem paths
- HTTP/HTTPS URLs
- Future: S3, Azure Blob Storage, Google Cloud Storage
"""
import asyncio
import hashlib
import logging
import mimetypes
import secrets
import aiohttp
import aiofiles
from pathlib import Path
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from sqlalchemy.orm import Session

from api.src.config import settings
from api.src.models import Evidence, Control
from api.src.workers.task_worker import update_progress

logger = logging.getLogger(__name__)


class EvidenceFetcher:
    """Fetch evidence files from various sources"""
    
    def __init__(self):
        self.base_path = Path(settings.EVIDENCE_STORAGE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.max_file_size_bytes = settings.EVIDENCE_MAX_FILE_SIZE_MB * 1024 * 1024
        self.allowed_extensions = {ext.lower() for ext in settings.EVIDENCE_ALLOWED_EXTENSIONS}
    
    def _validate_extension(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        extension = Path(filename).suffix.lower()
        if not extension:
            return False
        return extension in self.allowed_extensions
    
    def _build_target_dir(self, agency_id: int, control_id: int) -> Path:
        """Create and return the target directory for evidence"""
        target_dir = self.base_path / str(agency_id) / str(control_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir
    
    def _generate_filename(self, original_filename: str) -> str:
        """Generate a unique filename"""
        extension = Path(original_filename).suffix.lower()
        return f"{secrets.token_hex(16)}{extension}"
    
    async def fetch_from_url(
        self,
        url: str,
        agency_id: int,
        control_id: int,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch evidence file from HTTP/HTTPS URL.
        
        Args:
            url: Source URL
            agency_id: Agency ID for organization
            control_id: Control ID for categorization
            filename: Optional override filename
            
        Returns:
            Dict with file metadata (path, size, checksum, etc.)
        """
        logger.info(f"Fetching evidence from URL: {url}")
        
        # Parse URL and determine filename
        parsed_url = urlparse(url)
        if not filename:
            filename = Path(parsed_url.path).name or "downloaded_evidence"
        
        # Validate extension
        if not self._validate_extension(filename):
            raise ValueError(f"File type not allowed: {filename}")
        
        # Prepare target location
        target_dir = self._build_target_dir(agency_id, control_id)
        generated_name = self._generate_filename(filename)
        file_path = target_dir / generated_name
        
        # Download file
        sha256 = hashlib.sha256()
        total_bytes = 0
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=300)) as response:
                response.raise_for_status()
                
                # Get content type
                content_type = response.headers.get('Content-Type', 'application/octet-stream')
                
                # Stream download to file
                async with aiofiles.open(file_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(1024 * 1024):  # 1MB chunks
                        if not chunk:
                            break
                        
                        total_bytes += len(chunk)
                        if total_bytes > self.max_file_size_bytes:
                            await aiofiles.os.remove(file_path)
                            raise ValueError(
                                f"File exceeds size limit of {settings.EVIDENCE_MAX_FILE_SIZE_MB} MB"
                            )
                        
                        await f.write(chunk)
                        sha256.update(chunk)
        
        relative_path = str(file_path.relative_to(self.base_path))
        
        logger.info(f"Successfully downloaded {total_bytes} bytes to {relative_path}")
        
        return {
            "absolute_path": str(file_path),
            "relative_path": relative_path,
            "file_size": total_bytes,
            "checksum": sha256.hexdigest(),
            "storage_backend": "local",
            "mime_type": content_type,
            "original_filename": filename,
            "source_url": url
        }
    
    async def fetch_from_local_path(
        self,
        source_path: str,
        agency_id: int,
        control_id: int,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Copy evidence file from local filesystem.
        
        Args:
            source_path: Source file path on local filesystem
            agency_id: Agency ID for organization
            control_id: Control ID for categorization  
            filename: Optional override filename
            
        Returns:
            Dict with file metadata
        """
        logger.info(f"Fetching evidence from local path: {source_path}")
        
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        if not source.is_file():
            raise ValueError(f"Source path is not a file: {source_path}")
        
        # Determine filename
        if not filename:
            filename = source.name
        
        # Validate extension
        if not self._validate_extension(filename):
            raise ValueError(f"File type not allowed: {filename}")
        
        # Prepare target location
        target_dir = self._build_target_dir(agency_id, control_id)
        generated_name = self._generate_filename(filename)
        file_path = target_dir / generated_name
        
        # Copy file with checksum
        sha256 = hashlib.sha256()
        total_bytes = 0
        
        async with aiofiles.open(source, 'rb') as src:
            async with aiofiles.open(file_path, 'wb') as dst:
                while True:
                    chunk = await src.read(1024 * 1024)  # 1MB chunks
                    if not chunk:
                        break
                    
                    total_bytes += len(chunk)
                    if total_bytes > self.max_file_size_bytes:
                        await aiofiles.os.remove(file_path)
                        raise ValueError(
                            f"File exceeds size limit of {settings.EVIDENCE_MAX_FILE_SIZE_MB} MB"
                        )
                    
                    await dst.write(chunk)
                    sha256.update(chunk)
        
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        relative_path = str(file_path.relative_to(self.base_path))
        
        logger.info(f"Successfully copied {total_bytes} bytes to {relative_path}")
        
        return {
            "absolute_path": str(file_path),
            "relative_path": relative_path,
            "file_size": total_bytes,
            "checksum": sha256.hexdigest(),
            "storage_backend": "local",
            "mime_type": mime_type,
            "original_filename": filename,
            "source_path": source_path
        }
    
    async def fetch_evidence(
        self,
        source: str,
        source_type: str,
        agency_id: int,
        control_id: int,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch evidence from any supported source.
        
        Args:
            source: Source location (URL, path, etc.)
            source_type: Type of source ("url", "local", "s3", etc.)
            agency_id: Agency ID
            control_id: Control ID
            filename: Optional filename override
            
        Returns:
            Dict with file metadata
        """
        if source_type == "url":
            return await self.fetch_from_url(source, agency_id, control_id, filename)
        elif source_type == "local":
            return await self.fetch_from_local_path(source, agency_id, control_id, filename)
        elif source_type == "s3":
            raise NotImplementedError("S3 fetching not yet implemented")
        elif source_type == "azure":
            raise NotImplementedError("Azure Blob Storage fetching not yet implemented")
        else:
            raise ValueError(f"Unsupported source type: {source_type}")


async def handle_fetch_evidence_task(task_id: int, payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """
    Task handler for auto-fetching evidence.
    
    Payload structure:
    {
        "control_id": int,
        "sources": [
            {
                "url": "https://example.com/file.pdf",
                "type": "url",  # or "local", "s3", etc.
                "title": "Optional title",
                "description": "Optional description",
                "evidence_type": "Optional type",
                "filename": "Optional filename override"
            },
            ...
        ],
        "created_by": int  # User ID who initiated the task
    }
    
    Returns:
        Result with fetched evidence details
    """
    logger.info(f"Evidence fetch task {task_id} started")
    
    # Extract parameters
    control_id = payload.get("control_id")
    sources = payload.get("sources", [])
    created_by = payload.get("created_by")
    
    if not control_id:
        raise ValueError("control_id is required")
    
    if not sources:
        raise ValueError("sources list is required")
    
    # Get control
    control = db.query(Control).filter(Control.id == control_id).first()
    if not control:
        raise ValueError(f"Control {control_id} not found")
    
    logger.info(f"Fetching {len(sources)} evidence files for control {control_id}")
    
    # Initialize fetcher
    fetcher = EvidenceFetcher()
    
    # Track results
    results = {
        "fetched": [],
        "failed": [],
        "total": len(sources),
        "control_id": control_id
    }
    
    # Fetch each source
    for idx, source_config in enumerate(sources):
        try:
            await update_progress(
                task_id,
                int(((idx) / len(sources)) * 100),
                f"Fetching source {idx + 1}/{len(sources)}"
            )
            
            # Extract source details
            source = source_config.get("url") or source_config.get("path")
            source_type = source_config.get("type", "url")
            title = source_config.get("title")
            description = source_config.get("description")
            evidence_type = source_config.get("evidence_type")
            filename = source_config.get("filename")
            
            if not source:
                raise ValueError(f"Source URL/path missing for item {idx}")
            
            logger.info(f"Fetching from {source_type}: {source}")
            
            # Fetch the file
            file_meta = await fetcher.fetch_evidence(
                source=source,
                source_type=source_type,
                agency_id=control.agency_id,
                control_id=control.id,
                filename=filename
            )
            
            # Create evidence record
            db_evidence = Evidence(
                control_id=control.id,
                agency_id=control.agency_id,
                title=title or file_meta.get("original_filename", f"Evidence {idx + 1}"),
                description=description or f"Auto-fetched from {source}",
                evidence_type=evidence_type,
                file_path=file_meta["relative_path"],
                original_filename=file_meta.get("original_filename"),
                mime_type=file_meta.get("mime_type"),
                file_size=file_meta.get("file_size"),
                checksum=file_meta.get("checksum"),
                storage_backend=file_meta.get("storage_backend", "local"),
                uploaded_by=created_by,
                verified=False
            )
            
            db.add(db_evidence)
            db.commit()
            db.refresh(db_evidence)
            
            results["fetched"].append({
                "evidence_id": db_evidence.id,
                "source": source,
                "title": db_evidence.title,
                "file_size": file_meta["file_size"],
                "checksum": file_meta["checksum"]
            })
            
            logger.info(f"Successfully created evidence {db_evidence.id}")
        
        except Exception as e:
            logger.error(f"Failed to fetch source {idx}: {e}", exc_info=True)
            results["failed"].append({
                "source": source_config.get("url") or source_config.get("path"),
                "error": str(e)
            })
    
    await update_progress(task_id, 100, "All sources processed")
    
    logger.info(
        f"Evidence fetch task {task_id} completed: "
        f"{len(results['fetched'])} succeeded, {len(results['failed'])} failed"
    )
    
    return results


# Export the handler
__all__ = ["handle_fetch_evidence_task", "EvidenceFetcher"]
