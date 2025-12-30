"""
FastAPI dependencies
"""
from typing import Optional
from fastapi import Header

from app.models.user_keys import UserAPIKeys


async def get_user_api_keys(
    x_openai_api_key: Optional[str] = Header(None),
    x_anthropic_api_key: Optional[str] = Header(None),
    x_gemini_api_key: Optional[str] = Header(None),
    x_hf_api_key: Optional[str] = Header(None),
) -> UserAPIKeys:
    """
    Extract user-provided API keys from request headers

    Headers:
    - X-OpenAI-API-Key
    - X-Anthropic-API-Key
    - X-Gemini-API-Key
    - X-HF-API-Key
    """
    return UserAPIKeys(
        openai_api_key=x_openai_api_key,
        anthropic_api_key=x_anthropic_api_key,
        gemini_api_key=x_gemini_api_key,
        hf_api_key=x_hf_api_key,
    )
