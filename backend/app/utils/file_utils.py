import hashlib
import os
import re
import unicodedata
from typing import Tuple
import fitz  # PyMuPDF
from app.core.exceptions import FileValidationError


def sanitize_filename(filename: str) -> str:
    """
    Sanitize an untrusted filename to prevent path traversal,
    injection of special characters, or filesystem corruption.
    """
    if not filename:
        return "unnamed_document.pdf"

    # Normalize unicode
    filename = unicodedata.normalize("NFKD", filename)

    # Strip any directory components (/ or \)
    filename = os.path.basename(filename.replace("\\", "/"))

    # Remove non-alphanumeric characters except dot, dash, underscore
    filename = re.sub(r"[^\w\.\- ]", "_", filename)

    # Collapse multiple dots or spaces
    filename = re.sub(r"\.{2,}", ".", filename)
    filename = re.sub(r"\s+", " ", filename).strip()

    # Enforce safe length limit (100 characters)
    name, ext = os.path.splitext(filename)
    if len(name) > 80:
        name = name[:80]

    safe_name = f"{name}{ext}"
    if not safe_name.lower().endswith(".pdf"):
        safe_name += ".pdf"

    return safe_name


def compute_sha256(data: bytes) -> str:
    """Calculate the deterministic SHA-256 checksum of raw binary data."""
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.hexdigest()


def validate_pdf_file(data: bytes, original_filename: str, max_size_mb: int = 25) -> Tuple[str, int]:
    """
    Comprehensively validate an uploaded document:
    1. Check for empty payload
    2. Enforce file size limit
    3. Validate .pdf extension
    4. Check %PDF- magic bytes header
    5. Verify PDF structural readability with PyMuPDF
    Returns (sanitized_filename, page_count).
    """
    # 1. Empty check
    if not data or len(data) == 0:
        raise FileValidationError("Uploaded file is empty (0 bytes).")

    # 2. File size limit
    max_bytes = max_size_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise FileValidationError(
            f"File size ({len(data) / (1024 * 1024):.1f} MB) exceeds maximum allowed limit of {max_size_mb} MB."
        )

    # 3. Extension check
    if not original_filename or not original_filename.lower().endswith(".pdf"):
        raise FileValidationError(f"Invalid file extension for '{original_filename}'. Only PDF files are supported.")

    clean_name = sanitize_filename(original_filename)

    # 4. Magic bytes inspection
    if not data.startswith(b"%PDF-"):
        raise FileValidationError("File header does not match PDF specification (magic bytes missing).")

    # 5. Structural validation with PyMuPDF
    try:
        with fitz.open(stream=data, filetype="pdf") as doc:
            page_count = len(doc)
            if page_count == 0:
                raise FileValidationError("PDF document contains zero pages.")
    except Exception as e:
        if isinstance(e, FileValidationError):
            raise
        raise FileValidationError(f"Corrupted or unreadable PDF document: {str(e)}")

    return clean_name, page_count
