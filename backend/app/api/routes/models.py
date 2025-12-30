"""
Models API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends

from app.core.model_registry import ModelRegistry
from app.models.schemas import ModelsResponse
from app.models.user_keys import UserAPIKeys
from app.core.dependencies import get_user_api_keys

router = APIRouter()


@router.get("", response_model=ModelsResponse)
async def get_available_models(user_keys: UserAPIKeys = Depends(get_user_api_keys)):
    """
    Get list of available models based on API keys

    Combines server-side API keys with user-provided keys from headers.
    User keys take priority over server keys.
    """
    models = ModelRegistry.get_available_models(user_keys)
    return ModelsResponse(models=models)


@router.get("/default")
async def get_default_model(user_keys: UserAPIKeys = Depends(get_user_api_keys)):
    """
    Get the default model

    Returns first available model based on server + user API keys.
    """
    default_model = ModelRegistry.get_default_model(user_keys)
    if default_model is None:
        raise HTTPException(status_code=404, detail="No default model configured")
    return {"model_id": default_model}
