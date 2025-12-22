"""
Models API endpoints
"""
from fastapi import APIRouter

from app.core.model_registry import ModelRegistry
from app.models.schemas import ModelsResponse

router = APIRouter()


@router.get("", response_model=ModelsResponse)
async def get_available_models():
    """Get list of available models based on API keys"""
    models = ModelRegistry.get_available_models()
    return ModelsResponse(models=models)


@router.get("/default")
async def get_default_model():
    """Get the default model"""
    default_model = ModelRegistry.get_default_model()
    return {"model_id": default_model}
