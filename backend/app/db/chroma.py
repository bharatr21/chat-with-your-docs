"""
ChromaDB connection and configuration with HNSW
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from typing import Optional
import os

from app.config import settings


class ChromaDBManager:
    """Manage ChromaDB instance with HNSW indexing"""

    _instance: Optional['ChromaDBManager'] = None
    _client: Optional[chromadb.PersistentClient] = None
    _embeddings: Optional[HuggingFaceEmbeddings] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self._initialize()

    def _initialize(self):
        """Initialize ChromaDB client and embeddings"""
        # Ensure persist directory exists
        os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)

        # Initialize ChromaDB client with HNSW settings
        self._client = chromadb.PersistentClient(
            path=settings.CHROMA_DB_PATH,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )

        # Initialize embeddings
        self._embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

    def get_client(self) -> chromadb.PersistentClient:
        """Get ChromaDB client"""
        if self._client is None:
            self._initialize()
        return self._client

    def get_embeddings(self) -> HuggingFaceEmbeddings:
        """Get embeddings model"""
        if self._embeddings is None:
            self._initialize()
        return self._embeddings

    def get_collection(self, collection_name: Optional[str] = None):
        """Get or create a collection with HNSW configuration"""
        if collection_name is None:
            collection_name = settings.CHROMA_COLLECTION_NAME

        client = self.get_client()

        # HNSW configuration for optimal performance
        hnsw_config = {
            "hnsw:space": "cosine",
            "hnsw:construction_ef": 200,
            "hnsw:search_ef": 100,
            "hnsw:M": 16
        }

        # Get or create collection with HNSW metadata
        try:
            collection = client.get_or_create_collection(
                name=collection_name,
                metadata=hnsw_config
            )
        except Exception:
            collection = client.get_collection(name=collection_name)

        return collection

    def get_vectorstore(self, collection_name: Optional[str] = None) -> Chroma:
        """Get LangChain Chroma vectorstore"""
        if collection_name is None:
            collection_name = settings.CHROMA_COLLECTION_NAME

        embeddings = self.get_embeddings()

        vectorstore = Chroma(
            client=self.get_client(),
            collection_name=collection_name,
            embedding_function=embeddings,
        )

        return vectorstore

    def delete_collection(self, collection_name: Optional[str] = None):
        """Delete a collection"""
        if collection_name is None:
            collection_name = settings.CHROMA_COLLECTION_NAME

        client = self.get_client()
        try:
            client.delete_collection(name=collection_name)
        except Exception:
            pass  # Collection doesn't exist

    def reset(self):
        """Reset ChromaDB (delete all collections)"""
        if self._client:
            self._client.reset()


# Global instance
chroma_manager = ChromaDBManager()
