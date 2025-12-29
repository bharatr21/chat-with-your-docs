"""
Dynamic model registry based on available API keys
"""
from typing import List, Optional
from app.config import settings
from app.models.schemas import ModelInfo


class ModelRegistry:
    """Registry for available LLM models"""

    # Model definitions with their requirements
    MODEL_DEFINITIONS = {
        "mistralai/Mixtral-8x7B-Instruct-v0.1": {
            "name": "Mixtral 8x7B",
            "provider": "HuggingFace",
            "env_key": "HF_API_KEY",
            "description": "Mixtral 8x7B Instruct - Fast and efficient open-source model",
            "is_default": True
        },
        "gpt-5-mini": {
            "name": "GPT-5 Mini",
            "provider": "OpenAI",
            "env_key": "OPENAI_API_KEY",
            "description": "OpenAI's latest compact model with strong reasoning"
        },
        "claude-haiku-4-5": {
            "name": "Claude Haiku 4.5",
            "provider": "Anthropic",
            "env_key": "ANTHROPIC_API_KEY",
            "description": "Anthropic's fast and efficient Claude model"
        },
        "gemini-3-flash-preview": {
            "name": "Gemini 3 Flash",
            "provider": "Google",
            "env_key": "GEMINI_API_KEY",
            "description": "Google's latest multimodal model with 1M+ context"
        }
    }

    @classmethod
    def get_available_models(cls) -> List[ModelInfo]:
        """Get list of available models based on API keys"""
        models = []

        for model_id, config in cls.MODEL_DEFINITIONS.items():
            env_key = config["env_key"]

            # Check for API key availability
            if env_key == "HF_API_KEY":
                api_key = settings.get_hf_api_key()
            else:
                api_key = getattr(settings, env_key, None)

            available = bool(api_key)

            models.append(ModelInfo(
                id=model_id,
                name=config["name"],
                provider=config["provider"],
                available=available,
                description=config.get("description"),
                is_default=config.get("is_default", False)
            ))

        return models

    @classmethod
    def is_model_available(cls, model_id: str) -> bool:
        """Check if a specific model is available"""
        if model_id not in cls.MODEL_DEFINITIONS:
            return False

        config = cls.MODEL_DEFINITIONS[model_id]
        env_key = config["env_key"]

        if env_key == "HF_API_KEY":
            api_key = settings.get_hf_api_key()
        else:
            api_key = getattr(settings, env_key, None)

        return bool(api_key)

    @classmethod
    def get_default_model(cls) -> Optional[str]:
        """Get the first available model as default"""
        # Prefer HuggingFace (Mixtral) as default
        for model_id in [
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "gpt-5-mini",
            "claude-haiku-4-5",
            "gemini-3-flash-preview"
        ]:
            if cls.is_model_available(model_id):
                return model_id
        return None

    @classmethod
    def get_provider(cls, model_id: str) -> Optional[str]:
        """Get provider name for a model"""
        if model_id in cls.MODEL_DEFINITIONS:
            return cls.MODEL_DEFINITIONS[model_id]["provider"]
        return None

    @classmethod
    def get_env_key(cls, model_id: str) -> Optional[str]:
        """Get environment variable key for a model"""
        if model_id in cls.MODEL_DEFINITIONS:
            return cls.MODEL_DEFINITIONS[model_id]["env_key"]
        return None
