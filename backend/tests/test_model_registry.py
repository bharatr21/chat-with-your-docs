"""
Tests for model registry
"""
import pytest
from app.core.model_registry import ModelRegistry
from app.models.schemas import ModelInfo


class TestModelRegistry:
    """Test ModelRegistry functionality"""

    def test_model_definitions_exist(self):
        """Test that model definitions are properly configured"""
        assert len(ModelRegistry.MODEL_DEFINITIONS) > 0
        
        # Check expected models exist
        assert "mistralai/Mixtral-8x7B-Instruct-v0.1" in ModelRegistry.MODEL_DEFINITIONS
        assert "gpt-5-mini" in ModelRegistry.MODEL_DEFINITIONS
        assert "claude-4-5-haiku" in ModelRegistry.MODEL_DEFINITIONS
        assert "gemini-3-flash-preview" in ModelRegistry.MODEL_DEFINITIONS

    def test_model_definition_structure(self):
        """Test that each model definition has required fields"""
        for model_id, config in ModelRegistry.MODEL_DEFINITIONS.items():
            assert "name" in config
            assert "provider" in config
            assert "env_key" in config
            assert isinstance(config["name"], str)
            assert isinstance(config["provider"], str)
            assert isinstance(config["env_key"], str)

    def test_get_available_models_no_keys(self, monkeypatch):
        """Test getting available models when no API keys are set"""
        monkeypatch.setenv("HF_API_KEY", "")
        monkeypatch.setenv("OPENAI_API_KEY", "")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        monkeypatch.setenv("GEMINI_API_KEY", "")
        monkeypatch.setenv("DEFAULT_HF_API_KEY", "")
        
        models = ModelRegistry.get_available_models()
        
        assert isinstance(models, list)
        assert len(models) == len(ModelRegistry.MODEL_DEFINITIONS)
        
        # All models should be marked as unavailable
        for model in models:
            assert isinstance(model, ModelInfo)
            assert model.available is False

    def test_get_available_models_with_hf_key(self, monkeypatch):
        """Test getting available models with HuggingFace key"""
        monkeypatch.setenv("HF_API_KEY", "test_hf_key")
        monkeypatch.setenv("OPENAI_API_KEY", "")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        monkeypatch.setenv("GEMINI_API_KEY", "")
        
        models = ModelRegistry.get_available_models()
        
        # Find HuggingFace model
        hf_models = [m for m in models if m.provider == "HuggingFace"]
        assert len(hf_models) > 0
        assert all(m.available for m in hf_models)
        
        # Other models should be unavailable
        other_models = [m for m in models if m.provider != "HuggingFace"]
        assert all(not m.available for m in other_models)

    def test_get_available_models_with_multiple_keys(self, monkeypatch):
        """Test getting available models with multiple API keys"""
        monkeypatch.setenv("HF_API_KEY", "test_hf_key")
        monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        monkeypatch.setenv("GEMINI_API_KEY", "")
        
        models = ModelRegistry.get_available_models()
        
        available_models = [m for m in models if m.available]
        assert len(available_models) >= 2
        
        providers = {m.provider for m in available_models}
        assert "HuggingFace" in providers
        assert "OpenAI" in providers

    def test_is_model_available_true(self, monkeypatch):
        """Test checking if a model is available when key exists"""
        monkeypatch.setenv("HF_API_KEY", "test_key")
        
        assert ModelRegistry.is_model_available("mistralai/Mixtral-8x7B-Instruct-v0.1")

    def test_is_model_available_false(self, monkeypatch):
        """Test checking if a model is unavailable when key missing"""
        monkeypatch.setenv("OPENAI_API_KEY", "")
        
        assert not ModelRegistry.is_model_available("gpt-5-mini")

    def test_is_model_available_unknown_model(self):
        """Test checking availability of unknown model"""
        assert not ModelRegistry.is_model_available("unknown-model-id")

    def test_get_default_model_with_hf(self, monkeypatch):
        """Test getting default model when HF key is available"""
        monkeypatch.setenv("HF_API_KEY", "test_key")
        monkeypatch.setenv("OPENAI_API_KEY", "")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        monkeypatch.setenv("GEMINI_API_KEY", "")
        
        default = ModelRegistry.get_default_model()
        assert default == "mistralai/Mixtral-8x7B-Instruct-v0.1"

    def test_get_default_model_fallback(self, monkeypatch):
        """Test getting default model falls back to first available"""
        monkeypatch.setenv("HF_API_KEY", "")
        monkeypatch.setenv("DEFAULT_HF_API_KEY", "")
        monkeypatch.setenv("OPENAI_API_KEY", "test_key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        monkeypatch.setenv("GEMINI_API_KEY", "")
        
        default = ModelRegistry.get_default_model()
        assert default == "gpt-5-mini"

    def test_get_default_model_none(self, monkeypatch):
        """Test getting default model when no keys available"""
        monkeypatch.setenv("HF_API_KEY", "")
        monkeypatch.setenv("DEFAULT_HF_API_KEY", "")
        monkeypatch.setenv("OPENAI_API_KEY", "")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        monkeypatch.setenv("GEMINI_API_KEY", "")
        
        default = ModelRegistry.get_default_model()
        assert default is None

    def test_get_provider_valid_model(self):
        """Test getting provider for valid model"""
        provider = ModelRegistry.get_provider("gpt-5-mini")
        assert provider == "OpenAI"
        
        provider = ModelRegistry.get_provider("claude-4-5-haiku")
        assert provider == "Anthropic"

    def test_get_provider_invalid_model(self):
        """Test getting provider for invalid model"""
        provider = ModelRegistry.get_provider("invalid-model")
        assert provider is None

    def test_get_env_key_valid_model(self):
        """Test getting environment key for valid model"""
        env_key = ModelRegistry.get_env_key("gpt-5-mini")
        assert env_key == "OPENAI_API_KEY"
        
        env_key = ModelRegistry.get_env_key("mistralai/Mixtral-8x7B-Instruct-v0.1")
        assert env_key == "HF_API_KEY"

    def test_get_env_key_invalid_model(self):
        """Test getting environment key for invalid model"""
        env_key = ModelRegistry.get_env_key("invalid-model")
        assert env_key is None

    def test_model_info_fields(self, monkeypatch):
        """Test that ModelInfo objects have correct fields"""
        monkeypatch.setenv("HF_API_KEY", "test_key")
        
        models = ModelRegistry.get_available_models()
        
        for model in models:
            assert hasattr(model, "id")
            assert hasattr(model, "name")
            assert hasattr(model, "provider")
            assert hasattr(model, "available")
            assert isinstance(model.id, str)
            assert isinstance(model.name, str)
            assert isinstance(model.provider, str)
            assert isinstance(model.available, bool)

    def test_default_model_flag(self, monkeypatch):
        """Test that default model is properly flagged"""
        monkeypatch.setenv("HF_API_KEY", "test_key")
        
        models = ModelRegistry.get_available_models()
        
        # Find models marked as default
        default_models = [m for m in models if m.is_default]
        
        # Should have at least one default model
        assert len(default_models) >= 1
        
        # Default model should be Mixtral
        mixtral = next((m for m in models if "Mixtral" in m.name), None)
        assert mixtral is not None
        assert mixtral.is_default is True

    def test_with_default_hf_api_key(self, monkeypatch):
        """Test HF availability with DEFAULT_HF_API_KEY"""
        monkeypatch.setenv("HF_API_KEY", "")
        monkeypatch.setenv("DEFAULT_HF_API_KEY", "default_key")
        monkeypatch.setenv("OPENAI_API_KEY", "")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        monkeypatch.setenv("GEMINI_API_KEY", "")
        
        # HF model should be available via default key
        assert ModelRegistry.is_model_available("mistralai/Mixtral-8x7B-Instruct-v0.1")
        
        models = ModelRegistry.get_available_models()
        hf_models = [m for m in models if m.provider == "HuggingFace"]
        assert all(m.available for m in hf_models)