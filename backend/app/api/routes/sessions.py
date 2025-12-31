"""
Sessions API endpoints
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    SessionCreate,
    SessionDeleteResponse,
    SessionInfo,
    SessionListResponse,
)
from app.services.session import session_store

router = APIRouter()


@router.post("", response_model=SessionInfo)
async def create_session(request: SessionCreate):
    """Create a new chat session"""
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
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail="Session not found") from e


@router.delete("/{session_id}", response_model=SessionDeleteResponse)
async def delete_session(session_id: str):
    """Delete a session"""
    if not session_store.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    session_store.delete_session(session_id)
    return SessionDeleteResponse(
        id=session_id, status="deleted", message="Session deleted successfully"
    )
