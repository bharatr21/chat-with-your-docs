"""
Documents API endpoints
"""

import logging
import os
import re
import shutil
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import settings
from app.db.chroma import chroma_manager
from app.models.schemas import (
    DocumentDeleteResponse,
    DocumentInfo,
    DocumentListResponse,
    DocumentMetadata,
    DocumentUploadResponse,
)
from app.services.document import DocumentProcessor, metadata_manager
from app.services.session import session_store

logger = logging.getLogger(__name__)
router = APIRouter()

# Ensure uploads directory exists
UPLOADS_DIR = "./uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and other security issues.

    Args:
        filename: Original filename from user upload

    Returns:
        Sanitized filename safe for filesystem operations

    Security measures:
    - Removes all directory components (path traversal prevention)
    - Removes null bytes
    - Replaces or removes dangerous characters
    - Ensures filename is not empty after sanitization
    """
    # Remove any directory components (handles both / and \ separators)
    filename = os.path.basename(filename)

    # Remove null bytes (can cause issues in C-based filesystem APIs)
    filename = filename.replace("\x00", "")

    # Remove or replace potentially dangerous characters
    # Keep: letters, digits, dots, hyphens, underscores, spaces
    filename = re.sub(r"[^\w\s.-]", "_", filename)

    # Replace consecutive dots (prevents ../ patterns after sanitization)
    filename = re.sub(r"\.\.+", ".", filename)

    # Remove leading/trailing whitespace and dots (can cause issues on some systems)
    filename = filename.strip(". \t")

    # Ensure filename is not empty after sanitization
    if not filename:
        filename = "unnamed_file"

    # Limit filename length (filesystem limits, typically 255 bytes)
    max_length = 200  # Leave room for doc_id prefix
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        # Validate extension length to prevent negative truncation
        if len(ext) >= max_length:
            raise ValueError(f"File extension too long (max {max_length - 1} characters)")
        filename = name[: max_length - len(ext)] + ext

    return filename


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document"""
    # Validate filename exists
    if file.filename is None:
        raise HTTPException(status_code=400, detail="No filename provided in upload")

    # Sanitize filename to prevent path traversal and other security issues
    safe_filename = sanitize_filename(file.filename)

    # Validate file type (use sanitized filename)
    processor = DocumentProcessor()

    if not processor.is_supported(safe_filename):
        raise HTTPException(
            status_code=400, detail="Unsupported file type. Supported: PDF, DOCX, TXT, MD, CSV"
        )

    # Check file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE // (1024 * 1024)}MB",
        )

    # Generate document ID
    doc_id = str(uuid.uuid4())

    # Save file temporarily (use sanitized filename)
    file_path = os.path.join(UPLOADS_DIR, f"{doc_id}_{safe_filename}")

    chunks_added = False
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process document (use sanitized filename)
        chunks, metadata = processor.process_document(file_path, safe_filename, doc_id)

        # Add to vector store
        vectorstore = chroma_manager.get_vectorstore()
        vectorstore.add_documents(chunks)
        chunks_added = True

        # Save metadata
        metadata_manager.save_metadata(doc_id, metadata)

        # Create response (use sanitized filename)
        doc_metadata = DocumentMetadata(
            title=metadata.get("title", safe_filename),
            filename=safe_filename,
            file_size=file_size,
            file_type=metadata.get("file_type", "unknown"),
            page_count=metadata.get("page_count"),
            headers=metadata.get("headers", []),
            chunk_count=metadata.get("chunk_count"),
        )

        return DocumentUploadResponse(
            id=doc_id,
            filename=safe_filename,
            status="success",
            message="Document uploaded and processed successfully",
            metadata=doc_metadata,
        )

    except Exception as e:
        # Clean up on error - remove both file and ChromaDB entries
        if os.path.exists(file_path):
            os.remove(file_path)

        # Clean up orphaned chunks from ChromaDB if they were added
        if chunks_added:
            try:
                collection = chroma_manager.get_collection()
                collection.delete(where={"doc_id": doc_id})
                logger.info(f"Cleaned up orphaned chunks for doc_id: {doc_id}")
            except Exception as cleanup_error:
                # Log but don't fail if ChromaDB cleanup fails
                logger.error(
                    "Failed to clean up orphaned ChromaDB chunks",
                    extra={"doc_id": doc_id, "error": str(cleanup_error)},
                    exc_info=True,
                )

        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("", response_model=DocumentListResponse)
async def list_documents():
    """List all documents"""
    metadata_list = metadata_manager.list_all_metadata()

    documents = []
    for meta in metadata_list:
        doc_info = DocumentInfo(
            id=meta.get("id"),
            metadata=DocumentMetadata(
                title=meta.get("title", meta.get("filename", "Unknown")),
                filename=meta.get("filename", "Unknown"),
                file_size=meta.get("file_size", 0),
                file_type=meta.get("file_type", "unknown"),
                page_count=meta.get("page_count"),
                headers=meta.get("headers", []),
                chunk_count=meta.get("chunk_count"),
            ),
        )
        documents.append(doc_info)

    return DocumentListResponse(documents=documents, total=len(documents))


@router.get("/{document_id}", response_model=DocumentInfo)
async def get_document(document_id: str):
    """Get document by ID"""
    try:
        meta = metadata_manager.load_metadata(document_id)
        return DocumentInfo(
            id=document_id,
            metadata=DocumentMetadata(
                title=meta.get("title", meta.get("filename", "Unknown")),
                filename=meta.get("filename", "Unknown"),
                file_size=meta.get("file_size", 0),
                file_type=meta.get("file_type", "unknown"),
                page_count=meta.get("page_count"),
                headers=meta.get("headers", []),
                chunk_count=meta.get("chunk_count"),
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail="Document not found") from e


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(document_id: str):
    """Delete a document"""
    try:
        if not metadata_manager.exists(document_id):
            raise HTTPException(status_code=404, detail="Document not found")

        # Check if document is referenced by any active sessions
        sessions = session_store.list_sessions()
        referencing_sessions = [
            session.id for session in sessions if document_id in session.document_ids
        ]

        if referencing_sessions:
            session_count = len(referencing_sessions)
            detail = (
                f"Cannot delete document: referenced by {session_count} active session(s). "
                f"Delete or update the sessions first: {', '.join(referencing_sessions[:3])}"
                + ("..." if session_count > 3 else "")
            )
            raise HTTPException(status_code=409, detail=detail)

        # Delete from ChromaDB
        collection = chroma_manager.get_collection()
        collection.delete(where={"doc_id": document_id})

        # Delete metadata
        metadata_manager.delete_metadata(document_id)

        # Delete uploaded file
        for filename in os.listdir(UPLOADS_DIR):
            if filename.startswith(document_id):
                os.remove(os.path.join(UPLOADS_DIR, filename))

        return DocumentDeleteResponse(
            id=document_id, status="deleted", message="Document deleted successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
