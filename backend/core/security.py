"""
Security and Path Sanitization Utilities.
"""

import os
import re
import uuid
from pathlib import Path
from fastapi import HTTPException, status


def sanitize_filename(filename: str) -> str:
    """Removes dangerous characters and prepends UUID to prevent collisions and traversal."""
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]", "_", filename)
    cleaned = cleaned.strip("._")
    if not cleaned:
        cleaned = "unnamed"
    return f"{uuid.uuid4().hex[:8]}_{cleaned}"


def validate_file_size(content_length: int, max_mb: int = 25) -> None:
    """Enforces upload file size constraints."""
    max_bytes = max_mb * 1024 * 1024
    if content_length > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded file exceeds maximum permitted limit of {max_mb} MB."
        )


def ensure_safe_path(target_path: Path, base_dir: Path) -> Path:
    """Guarantees target file path resolves strictly within the authorized base directory."""
    resolved_target = target_path.resolve()
    resolved_base = base_dir.resolve()
    try:
        resolved_target.relative_to(resolved_base)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Illegal path traversal attempt detected."
        )
    return resolved_target
