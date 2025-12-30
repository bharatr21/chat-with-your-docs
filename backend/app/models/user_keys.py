"""
User-provided API keys model
"""
from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserAPIKeys(BaseModel):
    """User-provided API keys for LLM providers"""
    model_config = ConfigDict(frozen=True)

    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    hf_api_key: Optional[str] = None
