"""
Evidence Fetcher MCP Tool
Fetches evidence from URLs or local filesystem and stores in database.
"""

import os
import hashlib
import aiohttp
import aiofiles
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class EvidenceSource(BaseModel):
    """Evidence source specification"""
    type: str = Field(..., description="Type: 'url' or 'file'")
    location: str = Field(..., description="URL or file path")
    description: str = Field(default="", description="Description of evidence")
    control_id: int = Field(..., description="Control ID this evidence relates to")


class EvidenceFetcherInput(BaseModel):
    """Input schema for evidence fetcher tool"""
    sources: List[EvidenceSource] = Field(..., description="List of evidence sources to fetch")
    project_id: int = Field(..., description="Project ID for evidence storage")
    created_by: int = Field(..., description="User ID who initiated the fetch")


class EvidenceFetcherOutput(BaseModel):
    """Output schema for evidence fetcher tool"""
    success: bool
    evidence_ids: List[int] = Field(default_factory=list)
    checksums: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    total_fetched: int = 0
    total_failed: int = 0


class EvidenceFetcherTool:
    """
    MCP Tool: Evidence Fetcher
    
    Fetches evidence documents from URLs or local filesystem,
    calculates checksums, and stores metadata in database.
    """
    
    name = "fetch_evidence"
    description = "Fetch evidence documents from URLs or local filesystem"
    
    def __init__(self, db_connection_string: str, storage_path: str = "/app/evidence_storage"):
        """
        Initialize the evidence fetcher tool.
        
        Args:
            db_connection_string: PostgreSQL connection string
            storage_path: Path to store downloaded evidence files
        """
        self.db_connection_string = db_connection_string
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool input"""
        return EvidenceFetcherInput.model_json_schema()
    
    @property
    def output_schema(self) -> Dict[str, Any]:
        """Return JSON schema for tool output"""
        return EvidenceFetcherOutput.model_json_schema()
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the evidence fetcher tool.
        
        Args:
            params: Dictionary matching EvidenceFetcherInput schema
            
        Returns:
            Dictionary matching EvidenceFetcherOutput schema
        """
        # Validate input
        input_data = EvidenceFetcherInput(**params)
        
        evidence_ids = []
        checksums = []
        errors = []
        
        # Process each source
        for source in input_data.sources:
            try:
                if source.type == "url":
                    result = await self._fetch_from_url(
                        source.location,
                        source.control_id,
                        input_data.project_id,
                        input_data.created_by,
                        source.description
                    )
                elif source.type == "file":
                    result = await self._fetch_from_file(
                        source.location,
                        source.control_id,
                        input_data.project_id,
                        input_data.created_by,
                        source.description
                    )
                else:
                    raise ValueError(f"Unknown source type: {source.type}")
                
                evidence_ids.append(result["evidence_id"])
                checksums.append(result["checksum"])
                
            except Exception as e:
                errors.append(f"Failed to fetch {source.location}: {str(e)}")
        
        return EvidenceFetcherOutput(
            success=len(errors) == 0,
            evidence_ids=evidence_ids,
            checksums=checksums,
            errors=errors,
            total_fetched=len(evidence_ids),
            total_failed=len(errors)
        ).model_dump()
    
    async def _fetch_from_url(
        self,
        url: str,
        control_id: int,
        project_id: int,
        created_by: int,
        description: str
    ) -> Dict[str, Any]:
        """Fetch evidence from URL"""
        # Generate filename from URL
        filename = Path(url).name or f"evidence_{datetime.now().timestamp()}"
        filepath = self.storage_path / f"{project_id}_{control_id}_{filename}"
        
        # Download file
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                
                # Stream to file and calculate checksum
                sha256 = hashlib.sha256()
                async with aiofiles.open(filepath, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        await f.write(chunk)
                        sha256.update(chunk)
                
                checksum = sha256.hexdigest()
                file_size = filepath.stat().st_size
                mime_type = response.headers.get('Content-Type', 'application/octet-stream')
        
        # Store in database
        evidence_id = await self._store_evidence(
            control_id=control_id,
            project_id=project_id,
            created_by=created_by,
            description=description or f"Evidence from {url}",
            file_path=str(filepath),
            file_name=filename,
            file_size=file_size,
            file_type=mime_type,
            checksum=checksum,
            source_url=url
        )
        
        return {
            "evidence_id": evidence_id,
            "checksum": checksum,
            "file_path": str(filepath)
        }
    
    async def _fetch_from_file(
        self,
        source_path: str,
        control_id: int,
        project_id: int,
        created_by: int,
        description: str
    ) -> Dict[str, Any]:
        """Fetch evidence from local filesystem"""
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"File not found: {source_path}")
        
        # Generate destination path
        filename = source.name
        filepath = self.storage_path / f"{project_id}_{control_id}_{filename}"
        
        # Copy file and calculate checksum
        sha256 = hashlib.sha256()
        async with aiofiles.open(source, 'rb') as src:
            async with aiofiles.open(filepath, 'wb') as dst:
                while True:
                    chunk = await src.read(8192)
                    if not chunk:
                        break
                    await dst.write(chunk)
                    sha256.update(chunk)
        
        checksum = sha256.hexdigest()
        file_size = filepath.stat().st_size
        
        # Detect MIME type (simple detection)
        mime_type = self._detect_mime_type(filename)
        
        # Store in database
        evidence_id = await self._store_evidence(
            control_id=control_id,
            project_id=project_id,
            created_by=created_by,
            description=description or f"Evidence from {source_path}",
            file_path=str(filepath),
            file_name=filename,
            file_size=file_size,
            file_type=mime_type,
            checksum=checksum,
            source_url=None
        )
        
        return {
            "evidence_id": evidence_id,
            "checksum": checksum,
            "file_path": str(filepath)
        }
    
    async def _store_evidence(
        self,
        control_id: int,
        project_id: int,
        created_by: int,
        description: str,
        file_path: str,
        file_name: str,
        file_size: int,
        file_type: str,
        checksum: str,
        source_url: str = None
    ) -> int:
        """Store evidence metadata in database"""
        # Import here to avoid circular dependencies
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        
        engine = create_engine(self.db_connection_string)
        Session = sessionmaker(bind=engine)
        
        with Session() as session:
            # Get user's agency_id for proper access control
            user_query = text("SELECT agency_id FROM users WHERE id = :user_id")
            user_result = session.execute(user_query, {"user_id": created_by})
            user_agency_id = user_result.scalar_one()
            
            # Insert evidence record
            # Note: evidence table uses 'agency_id' instead of 'project_id',
            # 'original_filename' instead of 'file_name', 'mime_type' instead of 'file_type'
            # Using 'title' field for description as required column
            # Maker-Checker: Set verification_status='pending' and submitted_by
            query = text("""
                INSERT INTO evidence (
                    control_id, agency_id, title, description, file_path, 
                    original_filename, file_size, mime_type, checksum, 
                    uploaded_by, uploaded_at, submitted_by, 
                    verification_status, verified, created_at, updated_at
                )
                VALUES (
                    :control_id, :agency_id, :title, :description, :file_path, 
                    :original_filename, :file_size, :mime_type, :checksum, 
                    :uploaded_by, NOW(), :submitted_by,
                    'pending', FALSE, NOW(), NOW()
                )
                RETURNING id
            """)
            
            result = session.execute(query, {
                "control_id": control_id,
                "agency_id": user_agency_id,  # Use user's agency_id for proper access control
                "title": description or file_name,  # title is required
                "description": description,
                "file_path": file_path,
                "original_filename": file_name,
                "file_size": file_size,
                "mime_type": file_type,
                "checksum": checksum,
                "uploaded_by": created_by,
                "submitted_by": created_by  # Maker-checker: Set submitter
            })
            
            evidence_id = result.scalar_one()
            session.commit()
            
            return evidence_id
    
    def _detect_mime_type(self, filename: str) -> str:
        """Simple MIME type detection based on file extension"""
        ext_to_mime = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.txt': 'text/plain',
            '.csv': 'text/csv',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.zip': 'application/zip',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
        }
        
        ext = Path(filename).suffix.lower()
        return ext_to_mime.get(ext, 'application/octet-stream')
