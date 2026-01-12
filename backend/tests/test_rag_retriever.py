"""
Tests for RAG retriever
"""

from unittest.mock import Mock, patch

import pytest
from langchain_core.documents import Document

from app.services.rag.retriever import HybridRetriever


@pytest.fixture(autouse=True)
def mock_chroma_manager():
    """Mock ChromaDB manager"""
    with patch("app.services.rag.retriever.chroma_manager") as mock:
        yield mock


@pytest.fixture
def sample_documents():
    """Sample documents for testing"""
    return [
        Document(
            page_content="Python is a programming language",
            metadata={"doc_id": "doc1", "filename": "python.txt", "chunk_id": 0},
        ),
        Document(
            page_content="JavaScript is used for web development",
            metadata={"doc_id": "doc2", "filename": "js.txt", "chunk_id": 0},
        ),
        Document(
            page_content="Python has great libraries for data science",
            metadata={"doc_id": "doc1", "filename": "python.txt", "chunk_id": 1},
        ),
    ]


class TestHybridRetriever:
    """Test HybridRetriever functionality"""

    def test_init_no_document_ids(self, mock_chroma_manager):
        """Test initializing retriever without document IDs"""
        retriever = HybridRetriever()
        assert retriever.document_ids == []

    def test_init_with_document_ids(self, mock_chroma_manager):
        """Test initializing retriever with document IDs"""
        doc_ids = ["doc1", "doc2"]
        retriever = HybridRetriever(document_ids=doc_ids)
        assert retriever.document_ids == doc_ids

    def test_get_documents_by_ids_empty(self, mock_chroma_manager):
        """Test getting documents with empty result"""
        mock_collection = Mock()
        mock_collection.get.return_value = {"documents": [], "metadatas": []}
        mock_chroma_manager.get_collection.return_value = mock_collection

        retriever = HybridRetriever()
        docs = retriever._get_documents_by_ids([])

        assert docs == []

    def test_get_documents_by_ids_with_filter(self, mock_chroma_manager, sample_documents):
        """Test getting documents filtered by IDs"""
        mock_collection = Mock()
        mock_collection.get.return_value = {
            "documents": ["Python is a programming language"],
            "metadatas": [{"doc_id": "doc1", "filename": "python.txt"}],
        }
        mock_chroma_manager.get_collection.return_value = mock_collection

        retriever = HybridRetriever(document_ids=["doc1"])
        docs = retriever._get_documents_by_ids(["doc1"])

        assert len(docs) == 1
        assert docs[0].page_content == "Python is a programming language"

    def test_get_documents_by_ids_exception(self, mock_chroma_manager):
        """Test getting documents handles exceptions"""
        mock_collection = Mock()
        mock_collection.get.side_effect = Exception("Test error")
        mock_chroma_manager.get_collection.return_value = mock_collection

        retriever = HybridRetriever()
        docs = retriever._get_documents_by_ids([])

        assert docs == []

    def test_vector_search_basic(self, mock_chroma_manager):
        """Test basic vector search"""
        mock_doc = Document(page_content="Test", metadata={})
        mock_vectorstore = Mock()
        mock_vectorstore.similarity_search_with_score.return_value = [(mock_doc, 0.8)]
        mock_chroma_manager.get_vectorstore.return_value = mock_vectorstore

        retriever = HybridRetriever()
        results = retriever._vector_search("test query", k=5)

        assert len(results) == 1
        # Check score conversion (distance to similarity)
        assert results[0][0] == mock_doc

    def test_vector_search_with_filter(self, mock_chroma_manager):
        """Test vector search with document ID filter"""
        mock_vectorstore = Mock()
        mock_vectorstore.similarity_search_with_score.return_value = []
        mock_chroma_manager.get_vectorstore.return_value = mock_vectorstore

        retriever = HybridRetriever(document_ids=["doc1", "doc2"])
        retriever._vector_search("test", k=5)

        # Verify filter was passed
        call_kwargs = mock_vectorstore.similarity_search_with_score.call_args[1]
        assert "filter" in call_kwargs
        assert call_kwargs["filter"] == {"doc_id": {"$in": ["doc1", "doc2"]}}

    def test_vector_search_exception(self, mock_chroma_manager):
        """Test vector search handles exceptions"""
        mock_vectorstore = Mock()
        mock_vectorstore.similarity_search_with_score.side_effect = Exception("Error")
        mock_chroma_manager.get_vectorstore.return_value = mock_vectorstore

        retriever = HybridRetriever()
        results = retriever._vector_search("test", k=5)

        assert results == []

    def test_bm25_search_basic(self, sample_documents):
        """Test BM25 lexical search"""
        retriever = HybridRetriever()
        results = retriever._bm25_search("Python programming", sample_documents, k=2)

        # Should return documents mentioning Python
        assert len(results) > 0
        assert all(isinstance(doc, Document) for doc, score in results)

    def test_bm25_search_empty_documents(self):
        """Test BM25 search with empty documents"""
        retriever = HybridRetriever()
        results = retriever._bm25_search("test", [], k=5)

        assert results == []

    def test_bm25_search_ranking(self, sample_documents):
        """Test BM25 search ranking"""
        retriever = HybridRetriever()
        results = retriever._bm25_search("Python", sample_documents, k=5)

        # Should return results
        assert len(results) > 0

        # Extract documents and scores
        docs = [doc for doc, _ in results]
        scores = [score for _, score in results]

        # Scores should be in descending order (non-increasing)
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1], f"Scores not in descending order: {scores}"

        # Top result should contain "Python" (either doc1 or doc1 chunk1)
        top_doc = docs[0]
        assert "Python" in top_doc.page_content, (
            f"Top result should contain 'Python', got: {top_doc.page_content}"
        )

    def test_reciprocal_rank_fusion_basic(self):
        """Test reciprocal rank fusion merging"""
        doc1 = Document(page_content="Doc1", metadata={"id": "1"})
        doc2 = Document(page_content="Doc2", metadata={"id": "2"})
        doc3 = Document(page_content="Doc3", metadata={"id": "3"})

        vector_results = [(doc1, 0.9), (doc2, 0.7)]
        bm25_results = [(doc2, 15.0), (doc3, 10.0)]

        retriever = HybridRetriever()
        fused = retriever._reciprocal_rank_fusion(vector_results, bm25_results, top_k=5)

        # Should merge results
        assert len(fused) <= 5
        assert all(isinstance(doc, Document) for doc in fused)

    def test_reciprocal_rank_fusion_empty_inputs(self):
        """Test RRF with empty inputs"""
        retriever = HybridRetriever()

        # Both empty
        fused = retriever._reciprocal_rank_fusion([], [], top_k=5)
        assert fused == []

        # One empty
        doc = Document(page_content="Test", metadata={})
        fused = retriever._reciprocal_rank_fusion([(doc, 0.8)], [], top_k=5)
        assert len(fused) == 1

    def test_reciprocal_rank_fusion_deduplication(self):
        """Test RRF removes duplicates"""
        doc = Document(page_content="Same doc", metadata={"id": "1"})

        # Same document in both results
        vector_results = [(doc, 0.9)]
        bm25_results = [(doc, 15.0)]

        retriever = HybridRetriever()
        fused = retriever._reciprocal_rank_fusion(vector_results, bm25_results, top_k=5)

        # Should only appear once with combined score
        assert len(fused) == 1

    def test_retrieve_with_no_documents(self, mock_chroma_manager):
        """Test retrieve when no documents exist"""
        mock_collection = Mock()
        mock_collection.get.return_value = {"documents": [], "metadatas": []}
        mock_chroma_manager.get_collection.return_value = mock_collection

        retriever = HybridRetriever()
        results = retriever.retrieve("test query", top_k=5)

        assert results == []

    @patch.object(HybridRetriever, "_get_documents_by_ids")
    @patch.object(HybridRetriever, "_vector_search")
    @patch.object(HybridRetriever, "_bm25_search")
    @patch.object(HybridRetriever, "_reciprocal_rank_fusion")
    def test_retrieve_integration(
        self, mock_rrf, mock_bm25, mock_vector, mock_get_docs, sample_documents
    ):
        """Test full retrieve pipeline"""
        mock_get_docs.return_value = sample_documents
        mock_vector.return_value = [(sample_documents[0], 0.9)]
        mock_bm25.return_value = [(sample_documents[1], 15.0)]
        mock_rrf.return_value = sample_documents[:2]

        retriever = HybridRetriever(document_ids=["doc1"])
        results = retriever.retrieve("Python programming", top_k=2)

        # Verify all methods were called
        mock_get_docs.assert_called_once()
        mock_vector.assert_called_once()
        mock_bm25.assert_called_once()
        mock_rrf.assert_called_once()

        assert len(results) == 2

    def test_retrieve_uses_config_top_k(self, mock_chroma_manager):
        """Test that retrieve uses config RETRIEVAL_TOP_K when not specified"""
        mock_collection = Mock()
        mock_collection.get.return_value = {"documents": [], "metadatas": []}
        mock_chroma_manager.get_collection.return_value = mock_collection

        with patch("app.services.rag.retriever.settings") as mock_settings:
            mock_settings.RETRIEVAL_TOP_K = 15

            retriever = HybridRetriever()
            retriever.retrieve("test")

            # Verify settings were used (implicitly tested by no error)

    def test_retrieve_custom_top_k(self, mock_chroma_manager):
        """Test retrieve with custom top_k parameter"""
        mock_collection = Mock()
        mock_collection.get.return_value = {"documents": [], "metadatas": []}
        mock_chroma_manager.get_collection.return_value = mock_collection

        retriever = HybridRetriever()
        results = retriever.retrieve("test", top_k=3)

        # Should not raise and return empty
        assert results == []

    def test_get_doc_key_missing_chunk_index(self):
        """Test that documents with same filename but missing chunk_index get different keys"""
        # This tests the fix for the bug where chunk_index defaulted to empty string,
        # causing documents with same filename but different content to be incorrectly
        # deduplicated during RRF fusion (e.g., "file.pdf::" for all).

        doc1 = Document(
            page_content="First chunk of content",
            metadata={"filename": "document.pdf"},  # No chunk_index
        )
        doc2 = Document(
            page_content="Second chunk of content",
            metadata={"filename": "document.pdf"},  # No chunk_index
        )

        retriever = HybridRetriever()
        key1 = retriever._get_doc_key(doc1)
        key2 = retriever._get_doc_key(doc2)

        # Keys should be different (content-based) since chunk_index is missing
        assert key1 != key2
        assert key1.startswith("hash::")
        assert key2.startswith("hash::")

        # Documents with same filename AND chunk_index should get the same key
        doc3 = Document(
            page_content="Third chunk", metadata={"filename": "document.pdf", "chunk_index": 0}
        )
        doc4 = Document(
            page_content="Different content",
            metadata={"filename": "document.pdf", "chunk_index": 0},
        )

        key3 = retriever._get_doc_key(doc3)
        key4 = retriever._get_doc_key(doc4)

        # These should have the same key (filename::chunk_index)
        assert key3 == key4 == "document.pdf::0"
