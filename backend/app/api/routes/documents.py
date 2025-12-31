"""
Documents API endpoints
"""

import os
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

router = APIRouter()

# Ensure uploads directory exists
UPLOADS_DIR = "./uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document"""
    # Validate file
    processor = DocumentProcessor()

    if not processor.is_supported(file.filename):
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

    # Save file temporarily
    file_path = os.path.join(UPLOADS_DIR, f"{doc_id}_{file.filename}")

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process document
        chunks, metadata = processor.process_document(file_path, file.filename, doc_id)

        # Add to vector store
        vectorstore = chroma_manager.get_vectorstore()
        vectorstore.add_documents(chunks)

        # Save metadata
        metadata_manager.save_metadata(doc_id, metadata)

        # Create response
        doc_metadata = DocumentMetadata(
            title=metadata.get("title", file.filename),
            filename=file.filename,
            file_size=file_size,
            file_type=metadata.get("file_type", "unknown"),
            page_count=metadata.get("page_count"),
            headers=metadata.get("headers", []),
            chunk_count=metadata.get("chunk_count"),
        )

        return DocumentUploadResponse(
            id=doc_id,
            filename=file.filename,
            status="success",
            message="Document uploaded and processed successfully",
            metadata=doc_metadata,
        )

    except Exception as e:
        # Clean up on error
        if os.path.exists(file_path):
            os.remove(file_path)
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
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail="Document not found") from e


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(document_id: str):
    """Delete a document"""
    if not metadata_manager.exists(document_id):
        raise HTTPException(status_code=404, detail="Document not found")

    try:
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

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
