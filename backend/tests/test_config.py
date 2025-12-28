"""
Tests for application configuration
"""
import os
import pytest
from app.config import Settings


def test_settings_defaults():
    """Test default settings values"""
    settings = Settings()
    
    assert settings.APP_NAME == "RAG Chat API"
    assert settings.APP_VERSION == "0.1.0"
    assert settings.DEBUG is False
    assert settings.CORS_ORIGINS == "http://localhost:3000"
    assert settings.CHROMA_DB_PATH == "./chroma_db"
    assert settings.CHROMA_COLLECTION_NAME == "documents"
    assert settings.SESSION_STORAGE == "file"
    assert settings.SESSION_DIR == "./.sessions"
    assert settings.MAX_FILE_SIZE == 100 * 1024 * 1024
    assert settings.CHUNK_SIZE == 512
    assert settings.CHUNK_OVERLAP == 50
    assert settings.RETRIEVAL_TOP_K == 20
    assert settings.CONTEXT_PREFIX_ENABLED is True
    assert settings.EMBEDDING_MODEL == "sentence-transformers/all-MiniLM-L6-v2"
    assert settings.HOST == "0.0.0.0"
    assert settings.PORT == 8000


def test_settings_with_env_vars(monkeypatch):
    """Test settings loaded from environment variables"""
    monkeypatch.setenv("APP_NAME", "Test App")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("HF_API_KEY", "test_hf_key")
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
    
    settings = Settings()
    
    assert settings.APP_NAME == "Test App"
    assert settings.DEBUG is True
    assert settings.PORT == 9000
    assert settings.HF_API_KEY == "test_hf_key"
    assert settings.OPENAI_API_KEY == "test_openai_key"


def test_cors_origins_list_single():
    """Test parsing single CORS origin"""
    settings = Settings(CORS_ORIGINS="http://localhost:3000")
    assert settings.cors_origins_list == ["http://localhost:3000"]


def test_cors_origins_list_multiple():
    """Test parsing multiple CORS origins"""
    settings = Settings(CORS_ORIGINS="http://localhost:3000,https://example.com,http://app.local")
    expected = ["http://localhost:3000", "https://example.com", "http://app.local"]
    assert settings.cors_origins_list == expected


def test_cors_origins_list_with_spaces():
    """Test parsing CORS origins with spaces"""
    settings = Settings(CORS_ORIGINS=" http://localhost:3000 , https://example.com , http://app.local ")
    expected = ["http://localhost:3000", "https://example.com", "http://app.local"]
    assert settings.cors_origins_list == expected


def test_get_hf_api_key_with_user_key():
    """Test HF API key retrieval when user key is set"""
    settings = Settings(HF_API_KEY="user_key", DEFAULT_HF_API_KEY="default_key")
    assert settings.get_hf_api_key() == "user_key"


def test_get_hf_api_key_with_default():
    """Test HF API key retrieval falls back to default"""
    settings = Settings(DEFAULT_HF_API_KEY="default_key")
    assert settings.get_hf_api_key() == "default_key"


def test_get_hf_api_key_none():
    """Test HF API key retrieval when no keys set"""
    settings = Settings()
    assert settings.get_hf_api_key() is None


def test_api_keys_optional():
    """Test that API keys are optional"""
    settings = Settings()
    assert settings.HF_API_KEY is None
    assert settings.OPENAI_API_KEY is None
    assert settings.ANTHROPIC_API_KEY is None
    assert settings.GEMINI_API_KEY is None
    assert settings.DEFAULT_HF_API_KEY is None


def test_chunk_settings():
    """Test document chunking settings"""
    settings = Settings(CHUNK_SIZE=1024, CHUNK_OVERLAP=100)
    assert settings.CHUNK_SIZE == 1024
    assert settings.CHUNK_OVERLAP == 100


def test_retrieval_settings():
    """Test RAG retrieval settings"""
    settings = Settings(RETRIEVAL_TOP_K=10, CONTEXT_PREFIX_ENABLED=False)
    assert settings.RETRIEVAL_TOP_K == 10
    assert settings.CONTEXT_PREFIX_ENABLED is False


def test_file_size_limit():
    """Test file size limit configuration"""
    custom_size = 50 * 1024 * 1024  # 50MB
    settings = Settings(MAX_FILE_SIZE=custom_size)
    assert settings.MAX_FILE_SIZE == custom_size


def test_session_storage_configuration():
    """Test session storage configuration"""
    settings = Settings(SESSION_STORAGE="supabase", SESSION_DIR="/custom/path")
    assert settings.SESSION_STORAGE == "supabase"
    assert settings.SESSION_DIR == "/custom/path"


def test_chroma_configuration():
    """Test ChromaDB configuration"""
    settings = Settings(
        CHROMA_DB_PATH="/custom/chroma",
        CHROMA_COLLECTION_NAME="test_collection"
    )
    assert settings.CHROMA_DB_PATH == "/custom/chroma"
    assert settings.CHROMA_COLLECTION_NAME == "test_collection"


def test_embedding_model_configuration():
    """Test embedding model configuration"""
    custom_model = "sentence-transformers/all-mpnet-base-v2"
    settings = Settings(EMBEDDING_MODEL=custom_model)
    assert settings.EMBEDDING_MODEL == custom_model


def test_server_configuration():
    """Test server host and port configuration"""
    settings = Settings(HOST="127.0.0.1", PORT=5000)
    assert settings.HOST == "127.0.0.1"
    assert settings.PORT == 5000