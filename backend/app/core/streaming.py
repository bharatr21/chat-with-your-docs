"""
Vercel AI SDK compatible streaming protocol
"""

import json
import uuid
from collections.abc import AsyncIterator
from typing import Any


class VercelStreamFormatter:
    """Format streaming responses for Vercel AI SDK useChat hook"""

    @staticmethod
    async def format_stream(
        chunks: AsyncIterator[str], message_id: str | None = None
    ) -> AsyncIterator[str]:
        """
        Format streaming chunks to Vercel AI SDK protocol

        Protocol:
        - data: {"type": "text-delta", "id": "...", "delta": "..."}\n\n
        - data: [DONE]\n\n
        """
        if message_id is None:
            message_id = str(uuid.uuid4())

        try:
            async for chunk in chunks:
                if chunk:
                    # Format as Vercel AI SDK text-delta
                    delta_event = {"type": "text-delta", "id": message_id, "delta": chunk}
                    yield f"data: {json.dumps(delta_event)}\n\n"

            # Send completion marker
            yield "data: [DONE]\n\n"

        except Exception as e:
            # Send error event
            error_event = {"type": "error", "id": message_id, "error": str(e)}
            yield f"data: {json.dumps(error_event)}\n\n"

    @staticmethod
    def format_sources(sources: list[dict[str, Any]], message_id: str) -> str:
        """Format sources metadata event"""
        sources_event = {"type": "metadata", "id": message_id, "metadata": {"sources": sources}}
        return f"data: {json.dumps(sources_event)}\n\n"


class StreamBuffer:
    """Buffer for streaming LLM responses"""

    def __init__(self):
        self.buffer = []

    async def stream_chunks(self, llm_stream: AsyncIterator[str]) -> AsyncIterator[str]:
        """Stream chunks and buffer them"""
        async for chunk in llm_stream:
            self.buffer.append(chunk)
            yield chunk

    def get_full_response(self) -> str:
        """Get the complete buffered response"""
        return "".join(self.buffer)
