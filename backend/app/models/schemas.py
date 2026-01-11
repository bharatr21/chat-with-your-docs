"""
Pydantic schemas for request/response models
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

# ===== Chat Models =====


class Message(BaseModel):
    """Chat message"""

    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: datetime | None = Field(default_factory=datetime.now(timezone.utc))


class ChatRequest(BaseModel):
    """Request for chat endpoint"""

    messages: list[Message] = Field(..., description="Conversation history")
    model_id: str = Field(
        default="mistralai/Mixtral-8x7B-Instruct-v0.1", description="LLM model ID"
    )
    session_id: str | None = Field(None, description="Session ID for context")
    document_ids: list[str] = Field(default_factory=list, description="Document IDs for RAG")
    stream: bool = Field(default=True, description="Enable streaming response")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=4096)


class ChatResponse(BaseModel):
    """Response for chat endpoint (non-streaming)"""

    message: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    model_id: str
    session_id: str | None = None


# ===== Model Registry =====


class ModelInfo(BaseModel):
    """Information about an available model"""

    id: str
    name: str
    provider: str
    available: bool
    description: str | None = None
    is_default: bool = False


class ModelsResponse(BaseModel):
    """Response for models endpoint"""

    models: list[ModelInfo]


# ===== Document Models =====


class DocumentMetadata(BaseModel):
    """Document metadata"""

    title: str | None = None
    filename: str
    file_size: int
    file_type: str
    page_count: int | None = None
    headers: list[str] = Field(default_factory=list)
    upload_date: datetime = Field(default_factory=datetime.now(timezone.utc))
    chunk_count: int | None = None


class DocumentUploadResponse(BaseModel):
    """Response for document upload"""

    id: str
    filename: str
    status: str
    message: str
    metadata: DocumentMetadata


class DocumentInfo(BaseModel):
    """Document information"""

    id: str
    metadata: DocumentMetadata


class DocumentListResponse(BaseModel):
    """Response for list documents"""

    documents: list[DocumentInfo]
    total: int


class DocumentDeleteResponse(BaseModel):
    """Response for delete document"""

    id: str
    status: str
    message: str


# ===== Session Models =====


class SessionCreate(BaseModel):
    """Request to create a session"""

    name: str | None = Field(None, description="Session name")
    model_id: str = Field(
        default="mistralai/Mixtral-8x7B-Instruct-v0.1", description="Default model ID"
    )
    document_ids: list[str] = Field(default_factory=list, description="Document IDs")


class SessionInfo(BaseModel):
    """Session information"""

    id: str
    name: str | None = None
    model_id: str
    document_ids: list[str]
    messages: list[Message]
    created_at: datetime
    updated_at: datetime


class SessionListResponse(BaseModel):
    """Response for list sessions"""

    sessions: list[SessionInfo]
    total: int


class SessionDeleteResponse(BaseModel):
    """Response for delete session"""

    id: str
    status: str
    message: str


# ===== RAG Models =====


class RetrievedChunk(BaseModel):
    """Retrieved document chunk"""

    content: str
    metadata: dict[str, Any]
    score: float


class RAGContext(BaseModel):
    """RAG retrieval context"""

    chunks: list[RetrievedChunk]
    total_chunks: int
