"""
Hybrid retriever using HNSW (semantic) + BM25 (lexical) with RRF fusion
"""

import hashlib
import logging
import re
from typing import Any

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from app.config import settings
from app.db.chroma import chroma_manager

logger = logging.getLogger(__name__)

# Try to import NLTK for better tokenization
try:
    import nltk
    from nltk.tokenize import word_tokenize

    # Check if punkt tokenizer is available
    try:
        nltk.data.find("tokenizers/punkt")
        NLTK_AVAILABLE = True
    except LookupError:
        NLTK_AVAILABLE = False
except ImportError:
    NLTK_AVAILABLE = False


class HybridRetriever:
    """Hybrid retriever combining HNSW vector search and BM25 keyword search"""

    def __init__(self, document_ids: list[str] = None):
        self.document_ids = document_ids or []
        self.vectorstore = chroma_manager.get_vectorstore()

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        """Tokenize text for BM25 search using NLTK or fallback to regex."""
        if NLTK_AVAILABLE:
            try:
                tokens = word_tokenize(text.lower())
                return [token for token in tokens if re.search(r"\w", token)]
            except Exception:
                pass  # Fall through to regex tokenization

        # Fallback: regex-based tokenization
        return re.findall(r"\b\w+(?:'\w+)?\b", text.lower())

    def retrieve(self, query: str, top_k: int = None) -> list[Document]:
        """
        Retrieve relevant documents using hybrid search with RRF fusion

        Args:
            query: Search query
            top_k: Number of documents to retrieve

        Returns:
            List of retrieved documents
        """
        if top_k is None:
            top_k = settings.RETRIEVAL_TOP_K

        # Get all documents for the specified doc_ids
        all_docs = self._get_documents_by_ids(self.document_ids)

        if not all_docs:
            return []

        # Perform vector search (HNSW)
        vector_results = self._vector_search(query, top_k * 2)

        # Perform BM25 search
        bm25_results = self._bm25_search(query, all_docs, top_k * 2)

        # Fuse results using Reciprocal Rank Fusion (RRF)
        fused_results = self._reciprocal_rank_fusion(vector_results, bm25_results, top_k)

        return fused_results

    def _get_documents_by_ids(self, doc_ids: list[str]) -> list[Document]:
        """Get all chunks for specified document IDs"""
        collection = chroma_manager.get_collection()

        try:
            if doc_ids:
                # Filter by document IDs
                result = collection.get(
                    where={"doc_id": {"$in": doc_ids}}, include=["documents", "metadatas"]
                )
            else:
                # Get all documents
                result = collection.get(include=["documents", "metadatas"])

            if not result or not result.get("documents"):
                return []

            docs = []
            for i, doc_text in enumerate(result["documents"]):
                metadata = result["metadatas"][i] if result.get("metadatas") else {}
                docs.append(Document(page_content=doc_text, metadata=metadata))

            return docs

        except Exception as e:
            logger.error(
                "Failed to retrieve documents by IDs",
                extra={"doc_ids": doc_ids, "error": str(e)},
                exc_info=True,
            )
            return []

    def _vector_search(self, query: str, k: int) -> list[tuple]:
        """Perform HNSW vector similarity search"""
        try:
            filter_dict = None
            if self.document_ids:
                filter_dict = {"doc_id": {"$in": self.document_ids}}

            results = self.vectorstore.similarity_search_with_score(query, k=k, filter=filter_dict)

            # Convert scores to similarity (Chroma returns distance)
            return [(doc, 1.0 / (1.0 + score)) for doc, score in results]

        except Exception as e:
            logger.error(
                "Failed to perform vector search",
                extra={"query": query, "k": k, "doc_ids": self.document_ids, "error": str(e)},
                exc_info=True,
            )
            return []

    def _bm25_search(self, query: str, documents: list[Document], k: int) -> list[tuple]:
        """Perform BM25 keyword search"""
        if not documents:
            return []

        try:
            # Tokenize documents using improved tokenizer
            tokenized_docs = [self._tokenize(doc.page_content) for doc in documents]

            # Create BM25 index
            bm25 = BM25Okapi(tokenized_docs)

            # Tokenize query using improved tokenizer
            tokenized_query = self._tokenize(query)

            # Get BM25 scores
            scores = bm25.get_scores(tokenized_query)

            # Get top-k results
            doc_scores = list(zip(documents, scores, strict=True))
            doc_scores.sort(key=lambda x: x[1], reverse=True)

            return doc_scores[:k]

        except Exception as e:
            logger.error(
                "Failed to perform BM25 search",
                extra={
                    "query": query,
                    "k": k,
                    "num_documents": len(documents),
                    "error": str(e),
                },
                exc_info=True,
            )
            return []

    @staticmethod
    def _get_doc_key(doc: Document) -> str:
        """
        Generate a unique key for a document using metadata and content hash.

        Uses filename + chunk_index if available, otherwise falls back to content hash.
        This ensures documents with identical headers but different content are not merged.
        """
        # Try to use metadata for semantic identification
        filename = doc.metadata.get("filename", "")
        chunk_index = doc.metadata.get("chunk_index")

        if filename and chunk_index is not None:
            # Use filename and chunk index as primary key
            return f"{filename}::{chunk_index}"

        # Fall back to content hash for documents without proper metadata
        content_hash = hashlib.sha256(doc.page_content.encode()).hexdigest()[:16]
        return f"hash::{content_hash}"

    def _reciprocal_rank_fusion(
        self, vector_results: list[tuple], bm25_results: list[tuple], k: int, weight: float = 60.0
    ) -> list[Document]:
        """
        Combine results using Reciprocal Rank Fusion (RRF)

        RRF formula: score = sum(1 / (rank + k)) for each result list
        """
        doc_scores: dict[str, dict[str, Any]] = {}

        # Process vector search results
        for rank, (doc, _score) in enumerate(vector_results):
            doc_key = self._get_doc_key(doc)
            if doc_key not in doc_scores:
                doc_scores[doc_key] = {"doc": doc, "score": 0.0}
            doc_scores[doc_key]["score"] += 1.0 / (rank + weight)

        # Process BM25 results
        for rank, (doc, _score) in enumerate(bm25_results):
            doc_key = self._get_doc_key(doc)
            if doc_key not in doc_scores:
                doc_scores[doc_key] = {"doc": doc, "score": 0.0}
            doc_scores[doc_key]["score"] += 1.0 / (rank + weight)

        # Sort by fused score
        sorted_docs = sorted(doc_scores.values(), key=lambda x: x["score"], reverse=True)

        # Return top-k documents
        return [item["doc"] for item in sorted_docs[:k]]
