"""
Dynamic model registry based on available API keys
"""

from app.config import settings
from app.models.schemas import ModelInfo
from app.models.user_keys import UserAPIKeys


class ModelRegistry:
    """Registry for available LLM models"""

    # Model definitions with their requirements
    MODEL_DEFINITIONS = {
        "mistralai/Mixtral-8x7B-Instruct-v0.1": {
            "name": "Mixtral 8x7B",
            "provider": "HuggingFace",
            "env_key": "HF_API_KEY",
            "description": "Mixtral 8x7B Instruct - Fast and efficient open-source model",
            "is_default": True,
        },
        "gpt-5-mini": {
            "name": "GPT-5 Mini",
            "provider": "OpenAI",
            "env_key": "OPENAI_API_KEY",
            "description": "OpenAI's latest compact model with strong reasoning",
        },
        "claude-haiku-4-5": {
            "name": "Claude Haiku 4.5",
            "provider": "Anthropic",
            "env_key": "ANTHROPIC_API_KEY",
            "description": "Anthropic's fast and efficient Claude model",
        },
        "gemini-3-flash-preview": {
            "name": "Gemini 3 Flash",
            "provider": "Google",
            "env_key": "GEMINI_API_KEY",
            "description": "Google's latest multimodal model with 1M+ context",
        },
    }

    @classmethod
    def _get_api_key(cls, env_key: str, user_keys: UserAPIKeys | None = None) -> str | None:
        """
        Get API key with priority: user-provided > server settings

        Args:
            env_key: Environment key name (e.g., "OPENAI_API_KEY")
            user_keys: Optional user-provided API keys

        Returns:
            API key if available, None otherwise
        """
        # Check user-provided keys first
        if user_keys:
            if env_key == "OPENAI_API_KEY" and user_keys.openai_api_key:
                return user_keys.openai_api_key
            elif env_key == "ANTHROPIC_API_KEY" and user_keys.anthropic_api_key:
                return user_keys.anthropic_api_key
            elif env_key == "GEMINI_API_KEY" and user_keys.gemini_api_key:
                return user_keys.gemini_api_key
            elif env_key == "HF_API_KEY" and user_keys.hf_api_key:
                return user_keys.hf_api_key

        # Fall back to server settings
        if env_key == "HF_API_KEY":
            return settings.get_hf_api_key()
        else:
            return getattr(settings, env_key, None)

    @classmethod
    def get_available_models(cls, user_keys: UserAPIKeys | None = None) -> list[ModelInfo]:
        """
        Get list of available models based on API keys

        Args:
            user_keys: Optional user-provided API keys (priority over server keys)

        Returns:
            List of ModelInfo with availability based on merged keys
        """
        models = []

        for model_id, config in cls.MODEL_DEFINITIONS.items():
            env_key = config["env_key"]

            # Check for API key availability (user keys > server keys)
            api_key = cls._get_api_key(env_key, user_keys)
            available = bool(api_key)

            models.append(
                ModelInfo(
                    id=model_id,
                    name=config["name"],
                    provider=config["provider"],
                    available=available,
                    description=config.get("description"),
                    is_default=config.get("is_default", False),
                )
            )

        return models

    @classmethod
    def is_model_available(cls, model_id: str, user_keys: UserAPIKeys | None = None) -> bool:
        """
        Check if a specific model is available

        Args:
            model_id: Model identifier
            user_keys: Optional user-provided API keys

        Returns:
            True if model is available with current keys
        """
        if model_id not in cls.MODEL_DEFINITIONS:
            return False

        config = cls.MODEL_DEFINITIONS[model_id]
        env_key = config["env_key"]

        api_key = cls._get_api_key(env_key, user_keys)
        return bool(api_key)

    @classmethod
    def get_default_model(cls, user_keys: UserAPIKeys | None = None) -> str | None:
        """
        Get the first available model as default

        Args:
            user_keys: Optional user-provided API keys

        Returns:
            Default model ID or None if no models available
        """
        # Prefer HuggingFace (Mixtral) as default
        for model_id in [
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "gpt-5-mini",
            "claude-haiku-4-5",
            "gemini-3-flash-preview",
        ]:
            if cls.is_model_available(model_id, user_keys):
                return model_id
        return None

    @classmethod
    def get_provider(cls, model_id: str) -> str | None:
        """Get provider name for a model"""
        if model_id in cls.MODEL_DEFINITIONS:
            return cls.MODEL_DEFINITIONS[model_id]["provider"]
        return None

    @classmethod
    def get_env_key(cls, model_id: str) -> str | None:
        """Get environment variable key for a model"""
        if model_id in cls.MODEL_DEFINITIONS:
            return cls.MODEL_DEFINITIONS[model_id]["env_key"]
        return None
