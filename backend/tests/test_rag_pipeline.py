"""
Tests for RAG pipeline
"""

from unittest.mock import Mock, patch

import pytest
from langchain_core.documents import Document

from app.services.rag.pipeline import RAGPipeline


@pytest.fixture
def mock_llm_provider():
    """Mock LLM provider"""
    with patch("app.services.rag.pipeline.LLMProvider") as mock:
        yield mock


@pytest.fixture
def mock_retriever():
    """Mock hybrid retriever"""
    with patch("app.services.rag.pipeline.HybridRetriever") as mock:
        yield mock


@pytest.fixture
def sample_documents():
    """Sample retrieved documents"""
    return [
        Document(
            page_content="Python is a programming language",
            metadata={"filename": "python.txt", "chunk_index": 0, "chunk_total": 5},
        ),
        Document(
            page_content="It has many libraries",
            metadata={"filename": "python.txt", "chunk_index": 1, "chunk_total": 5},
        ),
    ]


class TestRAGPipeline:
    """Test RAG pipeline functionality"""

    def test_init_default_params(self, mock_llm_provider, mock_retriever):
        """Test pipeline initialization with defaults"""
        pipeline = RAGPipeline(model_id="test-model")

        assert pipeline.model_id == "test-model"
        assert pipeline.document_ids == []
        assert pipeline.temperature == 0.7
        assert pipeline.max_tokens == 1024

    def test_init_custom_params(self, mock_llm_provider, mock_retriever):
        """Test pipeline initialization with custom parameters"""
        pipeline = RAGPipeline(
            model_id="test-model", document_ids=["doc1", "doc2"], temperature=0.5, max_tokens=2048
        )

        assert pipeline.document_ids == ["doc1", "doc2"]
        assert pipeline.temperature == 0.5
        assert pipeline.max_tokens == 2048

    def test_init_creates_llm(self, mock_llm_provider, mock_retriever):
        """Test that initialization creates LLM instance"""
        pipeline = RAGPipeline(model_id="test-model")

        mock_llm_provider.create_llm.assert_called_once_with(
            model_id="test-model", temperature=0.7, max_tokens=1024, streaming=True, user_keys=None
        )

    def test_init_creates_retriever(self, mock_llm_provider, mock_retriever):
        """Test that initialization creates retriever"""
        doc_ids = ["doc1", "doc2"]
        pipeline = RAGPipeline(model_id="test-model", document_ids=doc_ids)

        mock_retriever.assert_called_once_with(document_ids=doc_ids)

    @pytest.mark.asyncio
    async def test_retrieve_context_basic(self, mock_llm_provider, sample_documents):
        """Test basic context retrieval"""
        with patch("app.services.rag.pipeline.HybridRetriever") as mock_retriever_class:
            mock_retriever = Mock()
            mock_retriever.retrieve.return_value = sample_documents
            mock_retriever_class.return_value = mock_retriever

            pipeline = RAGPipeline(model_id="test-model")
            docs, context = await pipeline.retrieve_context("test query", top_k=5)

            assert docs == sample_documents
            assert "Python is a programming language" in context
            assert "python.txt" in context

    @pytest.mark.asyncio
    async def test_retrieve_context_empty(self, mock_llm_provider):
        """Test context retrieval with no documents"""
        with patch("app.services.rag.pipeline.HybridRetriever") as mock_retriever_class:
            mock_retriever = Mock()
            mock_retriever.retrieve.return_value = []
            mock_retriever_class.return_value = mock_retriever

            pipeline = RAGPipeline(model_id="test-model")
            docs, context = await pipeline.retrieve_context("test query")

            assert docs == []
            assert context == "No relevant context found."

    @pytest.mark.asyncio
    async def test_retrieve_context_includes_source_info(self, mock_llm_provider, sample_documents):
        """Test that context includes source attribution"""
        with patch("app.services.rag.pipeline.HybridRetriever") as mock_retriever_class:
            mock_retriever = Mock()
            mock_retriever.retrieve.return_value = sample_documents
            mock_retriever_class.return_value = mock_retriever

            pipeline = RAGPipeline(model_id="test-model")
            _, context = await pipeline.retrieve_context("test")

            # Check for source markers
            assert "[Source 1:" in context
            assert "[Source 2:" in context
            assert "python.txt" in context

    @pytest.mark.asyncio
    async def test_retrieve_context_with_chunk_info(self, mock_llm_provider):
        """Test context includes chunk information when available"""
        docs = [
            Document(
                page_content="Content",
                metadata={"filename": "doc.pdf", "chunk_index": 4, "chunk_total": 10},
            )
        ]

        with patch("app.services.rag.pipeline.HybridRetriever") as mock_retriever_class:
            mock_retriever = Mock()
            mock_retriever.retrieve.return_value = docs
            mock_retriever_class.return_value = mock_retriever

            pipeline = RAGPipeline(model_id="test-model")
            _, context = await pipeline.retrieve_context("test")

            assert "Chunk 5/10" in context

    @pytest.mark.asyncio
    async def test_generate_response_streaming(self, mock_llm_provider):
        """Test streaming response generation"""
        mock_llm = Mock()

        async def mock_stream(*args, **kwargs):
            yield "Hello"
            yield " "
            yield "World"

        mock_llm.astream = mock_stream
        mock_llm_provider.create_llm.return_value = mock_llm
        mock_llm_provider.format_messages.return_value = []

        async def stream_response(llm, messages):
            async for chunk in mock_stream():
                yield chunk

        mock_llm_provider.stream_llm_response = stream_response

        with patch("app.services.rag.pipeline.HybridRetriever"):
            pipeline = RAGPipeline(model_id="test-model")

            result = []
            async for chunk in pipeline.generate_response(
                query="test", context="context", stream=True
            ):
                result.append(chunk)

            assert result == ["Hello", " ", "World"]

    @pytest.mark.asyncio
    async def test_generate_response_uses_prompt_template(self, mock_llm_provider):
        """Test that generate_response uses RAG prompt template"""
        mock_llm = Mock()

        async def mock_stream(*args, **kwargs):
            # Capture the messages passed
            messages = args[0] if args else kwargs.get("input", [])
            # Check that context and question are in messages
            assert any("test context" in str(m) for m in messages)
            yield "response"

        mock_llm.astream = mock_stream
        mock_llm_provider.create_llm.return_value = mock_llm
        mock_llm_provider.format_messages.return_value = [
            Mock(content="System: test context"),
            Mock(content="User: test query"),
        ]

        with patch("app.services.rag.pipeline.HybridRetriever"):
            pipeline = RAGPipeline(model_id="test-model")

            async for _ in pipeline.generate_response(query="test query", context="test context"):
                pass

    @pytest.mark.asyncio
    async def test_run_streaming(self, mock_llm_provider):
        """Test full pipeline with streaming"""
        mock_llm = Mock()

        async def mock_stream(*args, **kwargs):
            yield "Response"

        mock_llm.astream = mock_stream
        mock_llm_provider.create_llm.return_value = mock_llm
        mock_llm_provider.format_messages.return_value = []

        async def stream_response(llm, messages):
            async for chunk in mock_stream():
                yield chunk

        mock_llm_provider.stream_llm_response = stream_response

        with patch("app.services.rag.pipeline.HybridRetriever") as mock_retriever_class:
            mock_retriever = Mock()
            mock_retriever.retrieve.return_value = [
                Document(page_content="Context", metadata={"filename": "test.txt"})
            ]
            mock_retriever_class.return_value = mock_retriever

            pipeline = RAGPipeline(model_id="test-model")

            result = []
            async for chunk in pipeline.run(query="test", stream=True):
                result.append(chunk)

            assert "Response" in result

    @pytest.mark.asyncio
    async def test_run_with_conversation_history(self, mock_llm_provider):
        """Test pipeline with conversation history"""
        from app.models.schemas import Message

        mock_llm = Mock()

        async def mock_stream(*args, **kwargs):
            yield "Response"

        mock_llm.astream = mock_stream
        mock_llm_provider.create_llm.return_value = mock_llm
        mock_llm_provider.format_messages.return_value = []

        with patch("app.services.rag.pipeline.HybridRetriever") as mock_retriever_class:
            mock_retriever = Mock()
            mock_retriever.retrieve.return_value = []
            mock_retriever_class.return_value = mock_retriever

            history = [
                Message(role="user", content="Previous question"),
                Message(role="assistant", content="Previous answer"),
            ]

            pipeline = RAGPipeline(model_id="test-model")

            async for _ in pipeline.run(query="test", conversation_history=history):
                pass

            # Verify history was used (implicitly by no error)

    @pytest.mark.asyncio
    async def test_run_non_streaming(self, mock_llm_provider):
        """Test pipeline without streaming"""
        mock_llm = Mock()

        async def mock_invoke(*args, **kwargs):
            response = Mock()
            response.content = "Complete response"
            return response

        mock_llm.ainvoke = mock_invoke
        mock_llm_provider.create_llm.return_value = mock_llm
        mock_llm_provider.format_messages.return_value = []

        with patch("app.services.rag.pipeline.HybridRetriever") as mock_retriever_class:
            mock_retriever = Mock()
            mock_retriever.retrieve.return_value = []
            mock_retriever_class.return_value = mock_retriever

            pipeline = RAGPipeline(model_id="test-model")

            result = []
            async for chunk in pipeline.run(query="test", stream=False):
                result.append(chunk)

            # Should still yield chunks even in non-streaming mode
            assert len(result) > 0

    # Removed test_run_with_custom_top_k - top_k parameter no longer supported in run()

    def test_rag_prompt_structure(self):
        """Test RAG prompt template structure"""
        prompt = RAGPipeline.RAG_PROMPT

        # Verify prompt has system and user messages
        messages = prompt.format_messages(context="test context", question="test question")

        assert len(messages) >= 2
        # System message should contain context placeholder
        system_msg = str(messages[0])
        assert "context" in system_msg.lower() or "test context" in system_msg
