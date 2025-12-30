"""
Chat API endpoints with streaming support
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatRequest, Message
from app.models.user_keys import UserAPIKeys
from app.services.rag import RAGPipeline
from app.services.session import session_store
from app.core.streaming import VercelStreamFormatter
from app.core.model_registry import ModelRegistry
from app.core.dependencies import get_user_api_keys

router = APIRouter()


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
                detail="No available models. Please configure at least one API key."
            )

    # Get or create session
    if request.session_id and session_store.session_exists(request.session_id):
        session = session_store.get_session(request.session_id)
    else:
        session = None

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
            user_keys=user_keys
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
                        query=user_message.content,
                        conversation_history=history,
                        stream=True
                    ):
                        full_response.append(chunk)
                        yield chunk

                # Format entire stream (sends [DONE] only at the end)
                async for formatted in VercelStreamFormatter.format_stream(
                    buffered_stream()
                ):
                    yield formatted

                # Save messages to session if session exists
                if request.session_id:
                    # Add user message
                    session_store.add_message(request.session_id, user_message)
                    # Add assistant response
                    assistant_msg = Message(
                        role="assistant",
                        content="".join(full_response)
                    )
                    session_store.add_message(request.session_id, assistant_msg)

            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Vercel-AI-UI-Message-Stream": "v1",
                }
            )
        else:
            # Non-streaming response
            response_chunks = []
            async for chunk in pipeline.run(
                query=user_message.content,
                conversation_history=history,
                stream=False
            ):
                response_chunks.append(chunk)

            response_text = "".join(response_chunks)

            # Save to session
            if request.session_id:
                session_store.add_message(request.session_id, user_message)
                assistant_msg = Message(role="assistant", content=response_text)
                session_store.add_message(request.session_id, assistant_msg)

            return {
                "message": response_text,
                "model_id": request.model_id,
                "session_id": request.session_id
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
