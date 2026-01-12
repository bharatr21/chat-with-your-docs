"""
Application configuration using Pydantic Settings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Default HuggingFace API Key (for free tier access)
    DEFAULT_HF_API_KEY: str | None = None

    # API Keys for LLM Providers
    HF_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None

    # Application Settings
    APP_NAME: str = "RAG Chat API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # CORS Settings
    CORS_ORIGINS: str = "http://localhost:3000"

    # ChromaDB Settings
    CHROMA_DB_PATH: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "documents"

    # Session Settings
    SESSION_STORAGE: str = "file"
    SESSION_DIR: str = "./.sessions"

    # Document Processing Settings
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50

    # RAG Settings
    RETRIEVAL_TOP_K: int = 20
    CONTEXT_PREFIX_ENABLED: bool = True

    # Embedding Model
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    def get_hf_api_key(self) -> str | None:
        """Get HuggingFace API key with fallback to default"""
        return self.HF_API_KEY or self.DEFAULT_HF_API_KEY


# Global settings instance
settings = Settings()
