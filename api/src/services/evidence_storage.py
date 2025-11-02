import hashlib
import secrets
from pathlib import Path
from typing import Dict
from fastapi import HTTPException, UploadFile, status
from api.src.config import settings


class EvidenceStorageService:
    """Handle evidence file persistence for the compliance platform."""

    def __init__(self) -> None:
        self.backend = settings.EVIDENCE_STORAGE_BACKEND.lower()
        if self.backend != "local":
            raise NotImplementedError("Only local storage backend is implemented currently")
        self.base_path = Path(settings.EVIDENCE_STORAGE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.allowed_extensions = {ext.lower() for ext in settings.EVIDENCE_ALLOWED_EXTENSIONS}
        self.max_file_size_bytes = settings.EVIDENCE_MAX_FILE_SIZE_MB * 1024 * 1024

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

    def delete_file(self, relative_path: str) -> None:
        """Remove a stored evidence file from disk."""

        if not relative_path:
            return

        target_path = self.base_path / relative_path
        if target_path.is_file():
            target_path.unlink()

    def resolve_file_path(self, relative_path: str) -> Path:
        """Convert a stored relative path to an absolute path."""

        target_path = self.base_path / relative_path
        if not target_path.exists():
            raise FileNotFoundError("Evidence file not found")
        return target_path


evidence_storage_service = EvidenceStorageService()
