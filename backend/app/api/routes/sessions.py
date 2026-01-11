"""
Sessions API endpoints
"""

from fastapi import APIRouter, HTTPException

from app.core.model_registry import ModelRegistry
from app.models.schemas import (
    SessionCreate,
    SessionDeleteResponse,
    SessionInfo,
    SessionListResponse,
)
from app.services.document.metadata import metadata_manager
from app.services.session import session_store

router = APIRouter()


@router.post("", response_model=SessionInfo)
async def create_session(request: SessionCreate):
    """Create a new chat session"""
    # Validate model_id exists in ModelRegistry
    if request.model_id not in ModelRegistry.MODEL_DEFINITIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model_id: '{request.model_id}'. Model not found in registry.",
        )

    # Validate all document_ids exist - collect all invalid IDs for better UX
    invalid_doc_ids = []
    for doc_id in request.document_ids:
        try:
            if not metadata_manager.exists(doc_id):
                invalid_doc_ids.append(doc_id)
        except ValueError:
            # Invalid UUID format or path traversal attempt
            invalid_doc_ids.append(doc_id)

    if invalid_doc_ids:
        if len(invalid_doc_ids) == 1:
            detail = f"Invalid document_id: '{invalid_doc_ids[0]}'. Document not found."
        else:
            doc_list = "', '".join(invalid_doc_ids)
            detail = (
                f"Invalid document_ids: '{doc_list}'. "
                f"{len(invalid_doc_ids)} documents not found."
            )
        raise HTTPException(status_code=400, detail=detail)

    # All validations passed, create session
    session = session_store.create_session(
        model_id=request.model_id, document_ids=request.document_ids, name=request.name
    )
    return session


@router.get("", response_model=SessionListResponse)
async def list_sessions():
    """List all sessions"""
    sessions = session_store.list_sessions()
    return SessionListResponse(sessions=sessions, total=len(sessions))


@router.get("/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """Get session by ID"""
    try:
        session = session_store.get_session(session_id)
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail="Session not found") from e


@router.delete("/{session_id}", response_model=SessionDeleteResponse)
async def delete_session(session_id: str):
    """Delete a session"""
    try:
        if not session_store.session_exists(session_id):
            raise HTTPException(status_code=404, detail="Session not found")

        session_store.delete_session(session_id)
        return SessionDeleteResponse(
            id=session_id, status="deleted", message="Session deleted successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
