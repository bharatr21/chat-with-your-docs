"""
Chat API endpoints with streaming support
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.core.dependencies import get_user_api_keys
from app.core.model_registry import ModelRegistry
from app.core.streaming import VercelStreamFormatter
from app.models.schemas import ChatRequest, Message, SessionInfo
from app.models.user_keys import UserAPIKeys
from app.services.rag import RAGPipeline
from app.services.session import session_store

logger = logging.getLogger(__name__)
router = APIRouter()


def _persist_messages_to_session(
    session_id: str, user_message: Message, assistant_content: str, stream_mode: bool
) -> None:
    """Persist user and assistant messages to session with error handling."""
    try:
        session_store.add_message(session_id, user_message)
        assistant_msg = Message(role="assistant", content=assistant_content)
        session_store.add_message(session_id, assistant_msg)
    except (ValueError, FileNotFoundError) as e:
        mode = "streaming" if stream_mode else "non-streaming"
        logger.warning(
            f"Failed to persist messages to session after {mode} response",
            extra={
                "session_id": session_id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )


def _get_or_create_session(
    session_id: str | None, model_id: str, document_ids: list[str]
) -> tuple[SessionInfo | None, str | None]:
    """Get existing session or create new one. Returns (session, session_id)."""
    if not session_id:
        return None, None

    try:
        if session_store.session_exists(session_id):
            return session_store.get_session(session_id), session_id
    except ValueError:
        pass  # Invalid format, will create new

    # Create new session
    session = session_store.create_session(
        model_id=model_id, document_ids=document_ids or [], name=None
    )
    return session, session.id


@router.post("")
async def chat(request: ChatRequest, user_keys: UserAPIKeys = Depends(get_user_api_keys)):
    """
    Chat endpoint with RAG and streaming support.
    Compatible with Vercel AI SDK useChat hook.
    """
    # Validate model (check with user keys)
    if not ModelRegistry.is_model_available(request.model_id, user_keys):
        # Try to use default model
        default_model = ModelRegistry.get_default_model(user_keys)
        if default_model:
            request.model_id = default_model
        else:
            raise HTTPException(
                status_code=400,
                detail="No available models. Please configure at least one API key.",
            )

    # Get or create session
    session, new_session_id = _get_or_create_session(
        request.session_id, request.model_id, request.document_ids
    )
    if new_session_id:
        request.session_id = new_session_id

    # Get the last user message
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    user_message = request.messages[-1]
    if user_message.role != "user":
        raise HTTPException(status_code=400, detail="Last message must be from user")

    try:
        # Initialize RAG pipeline
        pipeline = RAGPipeline(
            model_id=request.model_id,
            document_ids=request.document_ids,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            user_keys=user_keys,
        )

        # Get conversation history: combine session history with request messages
        # Session messages provide full history, request messages may have recent context
        history = None
        if session and session.messages:
            # Use session's stored messages as history
            history = session.messages
        elif len(request.messages) > 1:
            # Fall back to request messages (excluding last) if no session
            history = request.messages[:-1]

        if request.stream:
            # Streaming response
            async def generate():
                full_response = []

                # Buffer chunks while streaming
                async def buffered_stream():
                    async for chunk in pipeline.run(
                        query=user_message.content, conversation_history=history, stream=True
                    ):
                        full_response.append(chunk)
                        yield chunk

                # Format entire stream (sends [DONE] only at the end)
                async for formatted in VercelStreamFormatter.format_stream(buffered_stream()):
                    yield formatted

                # Save messages to session if session exists
                if session is not None:
                    _persist_messages_to_session(
                        request.session_id, user_message, "".join(full_response), stream_mode=True
                    )

            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Vercel-AI-UI-Message-Stream": "v1",
                },
            )
        else:
            # Non-streaming response
            response_chunks = []
            async for chunk in pipeline.run(
                query=user_message.content, conversation_history=history, stream=False
            ):
                response_chunks.append(chunk)

            response_text = "".join(response_chunks)

            # Save to session
            if session is not None:
                _persist_messages_to_session(
                    request.session_id, user_message, response_text, stream_mode=False
                )

            return {
                "message": response_text,
                "model_id": request.model_id,
                "session_id": request.session_id,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error") from e
