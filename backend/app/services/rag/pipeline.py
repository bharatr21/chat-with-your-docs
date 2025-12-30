"""
LangChain RAG pipeline
"""
from typing import List, Optional, AsyncIterator
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

from app.services.llm.provider import LLMProvider
from app.services.rag.retriever import HybridRetriever
from app.models.schemas import Message, RetrievedChunk
from app.models.user_keys import UserAPIKeys


class RAGPipeline:
    """LangChain-based RAG pipeline"""

    RAG_PROMPT = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful AI assistant. Answer the user's question based on the provided context.
If the context doesn't contain relevant information, say so honestly. Always cite specific sources when possible.

Context:
{context}"""),
        ("user", "{question}")
    ])

    def __init__(
        self,
        model_id: str,
        document_ids: List[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        user_keys: Optional[UserAPIKeys] = None
    ):
        self.model_id = model_id
        self.document_ids = document_ids or []
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.user_keys = user_keys

        # Initialize components
        self.llm = LLMProvider.create_llm(
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=True,
            user_keys=user_keys
        )

        self.retriever = HybridRetriever(document_ids=document_ids)

    async def retrieve_context(self, query: str, top_k: int = 5) -> tuple:
        """
        Retrieve relevant context for query

        Returns:
            tuple: (retrieved_documents, formatted_context)
        """
        # Retrieve documents
        docs = self.retriever.retrieve(query, top_k=top_k)

        if not docs:
            return [], "No relevant context found."

        # Format context with source attribution
        context_parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("filename", "Unknown")
            chunk_index = doc.metadata.get("chunk_index")
            chunk_total = doc.metadata.get("chunk_total")
            source_info = f"[Source {i}: {source}"
            if chunk_index is not None and chunk_total is not None:
                source_info += f", Chunk {chunk_index + 1}/{chunk_total}"
            source_info += "]"
            context_parts.append(f"{source_info}\n{doc.page_content}")

        context = "\n\n".join(context_parts)

        return docs, context

    async def generate_response(
        self,
        query: str,
        context: str,
        stream: bool = True
    ) -> AsyncIterator[str]:
        """
        Generate response using LLM

        Args:
            query: User question
            context: Retrieved context
            stream: Enable streaming

        Yields:
            Response chunks
        """
        # Format prompt
        messages = self.RAG_PROMPT.format_messages(
            context=context,
            question=query
        )

        # Convert to LangChain messages
        lc_messages = LLMProvider.format_messages([
            {"role": "system", "content": messages[0].content},
            {"role": "user", "content": messages[1].content}
        ])

        # Stream response
        if stream:
            async for chunk in LLMProvider.stream_llm_response(self.llm, lc_messages):
                yield chunk
        else:
            response = await self.llm.ainvoke(lc_messages)
            yield response.content

    async def run(
        self,
        query: str,
        conversation_history: Optional[List[Message]] = None,
        stream: bool = True
    ) -> AsyncIterator[str]:
        """
        Run complete RAG pipeline

        Args:
            query: User question
            conversation_history: Previous messages
            stream: Enable streaming

        Yields:
            Response chunks
        """
        # Retrieve context
        docs, context = await self.retrieve_context(query)

        # Add conversation history to context if available
        if conversation_history:
            history_text = self._format_conversation_history(conversation_history)
            full_context = f"{history_text}\n\n{context}"
        else:
            full_context = context

        # Generate response
        async for chunk in self.generate_response(query, full_context, stream):
            yield chunk

    def _format_conversation_history(self, messages: List[Message]) -> str:
        """Format conversation history for context"""
        history_parts = ["Previous conversation:"]

        for msg in messages[-4:]:  # Last 4 messages for context
            role = msg.role.capitalize()
            history_parts.append(f"{role}: {msg.content}")

        return "\n".join(history_parts)

    def get_retrieved_chunks(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        """Get retrieved chunks with metadata for client"""
        docs = self.retriever.retrieve(query, top_k=top_k)

        chunks = []
        for doc in docs:
            chunks.append(RetrievedChunk(
                content=doc.page_content,
                metadata=doc.metadata,
                score=0.0
            ))

        return chunks
