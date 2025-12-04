import hashlib
import secrets
from pathlib import Path
from typing import Dict, Optional
from fastapi import HTTPException, UploadFile, status
from api.src.config import settings
import logging

logger = logging.getLogger(__name__)


class EvidenceStorageService:
    """Handle evidence file persistence for the compliance platform."""

    def __init__(self) -> None:
        self.backend = settings.EVIDENCE_STORAGE_BACKEND.lower()
        self.allowed_extensions = {ext.lower() for ext in settings.EVIDENCE_ALLOWED_EXTENSIONS}
        self.max_file_size_bytes = settings.EVIDENCE_MAX_FILE_SIZE_MB * 1024 * 1024
        
        if self.backend == "local":
            self.base_path = Path(settings.EVIDENCE_STORAGE_PATH)
            self.base_path.mkdir(parents=True, exist_ok=True)
            self.blob_service_client = None
        elif self.backend == "azure":
            self._init_azure_storage()
            self.base_path = None
        else:
            raise NotImplementedError(f"Storage backend '{self.backend}' is not supported")
    
    def _init_azure_storage(self) -> None:
        """Initialize Azure Blob Storage client with Managed Identity."""
        try:
            from azure.storage.blob import BlobServiceClient
            from azure.identity import DefaultAzureCredential
            
            # Use Managed Identity in Azure, or connection string for local dev
            if settings.AZURE_STORAGE_CONNECTION_STRING:
                logger.info("Initializing Azure Blob Storage with connection string")
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    settings.AZURE_STORAGE_CONNECTION_STRING
                )
            else:
                # Use Managed Identity in Azure Container Apps
                logger.info("Initializing Azure Blob Storage with Managed Identity")
                account_url = f"https://{settings.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
                credential = DefaultAzureCredential()
                self.blob_service_client = BlobServiceClient(
                    account_url=account_url,
                    credential=credential
                )
        except ImportError:
            raise ImportError(
                "Azure storage dependencies not installed. "
                "Install with: pip install azure-storage-blob azure-identity"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Azure Blob Storage: {e}")
            raise

    def _validate_extension(self, filename: str) -> None:
        extension = Path(filename).suffix.lower()
        if extension not in self.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{extension}' is not supported"
            )

    def _build_target_dir(self, agency_id: int, control_id: int) -> Path:
        target_dir = self.base_path / str(agency_id) / str(control_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir

    async def save_file(
        self,
        upload_file: UploadFile,
        agency_id: int,
        control_id: int
    ) -> Dict[str, object]:
        """Persist upload file to the configured backend and return metadata."""

        if not upload_file.filename:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename")

        self._validate_extension(upload_file.filename)

        if self.backend == "local":
            return await self._save_file_local(upload_file, agency_id, control_id)
        elif self.backend == "azure":
            return await self._save_file_azure(upload_file, agency_id, control_id)
        else:
            raise NotImplementedError(f"Backend '{self.backend}' not implemented")

    async def _save_file_local(
        self,
        upload_file: UploadFile,
        agency_id: int,
        control_id: int
    ) -> Dict[str, object]:
        """Save file to local filesystem."""
        target_dir = self._build_target_dir(agency_id, control_id)
        extension = Path(upload_file.filename).suffix.lower()
        generated_name = f"{secrets.token_hex(16)}{extension}"
        file_path = target_dir / generated_name

        sha256 = hashlib.sha256()
        total_bytes = 0

        with file_path.open("wb") as destination:
            while True:
                chunk = await upload_file.read(1024 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > self.max_file_size_bytes:
                    file_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds size limit of {settings.EVIDENCE_MAX_FILE_SIZE_MB} MB"
                    )
                destination.write(chunk)
                sha256.update(chunk)

        await upload_file.close()

        relative_path = str(file_path.relative_to(self.base_path))
        return {
            "absolute_path": str(file_path),
            "relative_path": relative_path,
            "file_size": total_bytes,
            "checksum": sha256.hexdigest(),
            "storage_backend": self.backend,
        }

    async def _save_file_azure(
        self,
        upload_file: UploadFile,
        agency_id: int,
        control_id: int
    ) -> Dict[str, object]:
        """Save file to Azure Blob Storage."""
        extension = Path(upload_file.filename).suffix.lower()
        generated_name = f"{secrets.token_hex(16)}{extension}"
        blob_name = f"{agency_id}/{control_id}/{generated_name}"
        
        container_name = settings.AZURE_STORAGE_CONTAINER_EVIDENCE
        container_client = self.blob_service_client.get_container_client(container_name)
        
        # Ensure container exists
        try:
            container_client.create_container()
        except Exception:
            pass  # Container already exists
        
        blob_client = container_client.get_blob_client(blob_name)
        
        sha256 = hashlib.sha256()
        total_bytes = 0
        chunks = []

        # Read file in chunks and validate size
        while True:
            chunk = await upload_file.read(1024 * 1024)
            if not chunk:
                break
            total_bytes += len(chunk)
            if total_bytes > self.max_file_size_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File exceeds size limit of {settings.EVIDENCE_MAX_FILE_SIZE_MB} MB"
                )
            chunks.append(chunk)
            sha256.update(chunk)

        # Upload to Azure Blob Storage
        try:
            blob_data = b''.join(chunks)
            blob_client.upload_blob(blob_data, overwrite=True)
            logger.info(f"Uploaded blob: {blob_name} ({total_bytes} bytes)")
        except Exception as e:
            logger.error(f"Failed to upload blob {blob_name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file to Azure: {str(e)}"
            )

        await upload_file.close()

        return {
            "absolute_path": blob_client.url,
            "relative_path": blob_name,
            "file_size": total_bytes,
            "checksum": sha256.hexdigest(),
            "storage_backend": self.backend,
        }

    def delete_file(self, relative_path: str) -> None:
        """Remove a stored evidence file from disk or Azure Blob Storage."""

        if not relative_path:
            return

        if self.backend == "local":
            target_path = self.base_path / relative_path
            if target_path.is_file():
                target_path.unlink()
        elif self.backend == "azure":
            container_name = settings.AZURE_STORAGE_CONTAINER_EVIDENCE
            container_client = self.blob_service_client.get_container_client(container_name)
            blob_client = container_client.get_blob_client(relative_path)
            try:
                blob_client.delete_blob()
                logger.info(f"Deleted blob: {relative_path}")
            except Exception as e:
                logger.warning(f"Failed to delete blob {relative_path}: {e}")

    def resolve_file_path(self, relative_path: str) -> Path:
        """Convert a stored relative path to an absolute path (local only)."""
        
        if self.backend == "azure":
            raise NotImplementedError("resolve_file_path not supported for Azure backend")

        target_path = self.base_path / relative_path
        if not target_path.exists():
            raise FileNotFoundError("Evidence file not found")
        return target_path
    
    def download_file(self, relative_path: str) -> bytes:
        """Download file content from storage (works for both local and Azure)."""
        
        if self.backend == "local":
            target_path = self.base_path / relative_path
            if not target_path.exists():
                raise FileNotFoundError(f"Evidence file not found: {relative_path}")
            with open(target_path, "rb") as f:
                return f.read()
                
        elif self.backend == "azure":
            container_name = settings.AZURE_STORAGE_CONTAINER_EVIDENCE
            container_client = self.blob_service_client.get_container_client(container_name)
            blob_client = container_client.get_blob_client(relative_path)
            
            try:
                download_stream = blob_client.download_blob()
                return download_stream.readall()
            except Exception as e:
                raise FileNotFoundError(f"Failed to download from Azure: {e}")
        else:
            raise NotImplementedError(f"download_file not supported for backend '{self.backend}'")
    
    def get_file_url(self, relative_path: str) -> str:
        """Get a URL to access the file (useful for Azure)."""
        
        if self.backend == "local":
            return f"/evidence/download/{relative_path}"
        elif self.backend == "azure":
            container_name = settings.AZURE_STORAGE_CONTAINER_EVIDENCE
            container_client = self.blob_service_client.get_container_client(container_name)
            blob_client = container_client.get_blob_client(relative_path)
            return blob_client.url
        else:
            raise NotImplementedError(f"get_file_url not supported for backend '{self.backend}'")


evidence_storage_service = EvidenceStorageService()
