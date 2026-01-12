"""
Tests for application configuration
"""

import importlib

from app.config import Settings


def test_settings_defaults():
    """Test default settings values"""
    settings = Settings()

    assert settings.APP_NAME == "RAG Chat API"
    assert settings.APP_VERSION == "0.1.0"
    assert settings.DEBUG is False
    assert settings.CORS_ORIGINS == "http://localhost:3000"
    # CHROMA_DB_PATH is set by conftest.py to a temp directory in tests
    assert settings.CHROMA_DB_PATH is not None
    assert settings.CHROMA_COLLECTION_NAME == "documents"
    assert settings.SESSION_STORAGE == "file"
    # SESSION_DIR default or test override
    assert settings.SESSION_DIR is not None
    assert settings.MAX_FILE_SIZE == 100 * 1024 * 1024
    assert settings.CHUNK_SIZE == 512
    assert settings.CHUNK_OVERLAP == 50
    assert settings.RETRIEVAL_TOP_K == 20
    assert settings.CONTEXT_PREFIX_ENABLED is True
    assert settings.EMBEDDING_MODEL == "sentence-transformers/all-MiniLM-L6-v2"
    assert settings.HOST == "0.0.0.0"
    assert settings.PORT == 8000


def test_settings_class_with_env_vars(monkeypatch):
    """Test Settings class instantiation with environment variables"""
    monkeypatch.setenv("APP_NAME", "Test App")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("HF_API_KEY", "test_hf_key")
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")

    # Create new instance to pick up env vars
    settings = Settings()

    assert settings.APP_NAME == "Test App"
    assert settings.DEBUG is True
    assert settings.PORT == 9000
    assert settings.HF_API_KEY == "test_hf_key"
    assert settings.OPENAI_API_KEY == "test_openai_key"


def test_module_level_settings_with_reload(monkeypatch):
    """Test that module-level settings instance picks up env vars after reload"""
    monkeypatch.setenv("APP_NAME", "Reloaded App")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("PORT", "8888")

    # Reload the config module to recreate the global settings instance
    import app.config

    importlib.reload(app.config)

    # Now the module-level settings should have the new values
    assert app.config.settings.APP_NAME == "Reloaded App"
    assert app.config.settings.DEBUG is True
    assert app.config.settings.PORT == 8888

    # Reload again to restore defaults for other tests
    monkeypatch.delenv("APP_NAME", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)
    monkeypatch.delenv("PORT", raising=False)
    importlib.reload(app.config)


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
    settings = Settings(
        CORS_ORIGINS=" http://localhost:3000 , https://example.com , http://app.local "
    )
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


def test_get_hf_api_key_none(monkeypatch):
    """Test HF API key retrieval when no keys set"""
    # Clear environment variables that might be set by conftest
    monkeypatch.delenv("DEFAULT_HF_API_KEY", raising=False)
    monkeypatch.delenv("HF_API_KEY", raising=False)
    # Prevent loading from .env file by passing _env_file=None
    settings = Settings(_env_file=None)
    assert settings.get_hf_api_key() is None


def test_api_keys_optional(monkeypatch):
    """Test that API keys are optional"""
    # Clear environment variables that might be set by conftest
    monkeypatch.delenv("DEFAULT_HF_API_KEY", raising=False)
    monkeypatch.delenv("HF_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    # Prevent loading from .env file by passing _env_file=None
    settings = Settings(_env_file=None)
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
    settings = Settings(CHROMA_DB_PATH="/custom/chroma", CHROMA_COLLECTION_NAME="test_collection")
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
