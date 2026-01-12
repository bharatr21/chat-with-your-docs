"""
User-provided API keys model
"""

from pydantic import BaseModel, ConfigDict


class UserAPIKeys(BaseModel):
    """User-provided API keys for LLM providers"""

    model_config = ConfigDict(frozen=True)

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None
    hf_api_key: str | None = None
