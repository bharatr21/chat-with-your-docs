"""
Tests for LLM provider factory
"""

from unittest.mock import Mock, patch

import pytest

from app.models.schemas import Message
from app.services.llm.provider import LLMProvider


class TestLLMProvider:
    """Test LLM provider functionality"""

    def test_create_llm_invalid_model(self):
        """Test creating LLM with unavailable model raises error"""
        with pytest.raises(ValueError) as exc:
            LLMProvider.create_llm("unavailable-model")

        assert "not available" in str(exc.value).lower()

    @patch("app.services.llm.provider.ModelRegistry.is_model_available")
    @patch("app.services.llm.provider.ModelRegistry.get_provider")
    @patch("app.services.llm.provider.ChatOpenAI")
    def test_create_openai_llm(
        self, mock_openai, mock_get_provider, mock_is_available, monkeypatch
    ):
        """Test creating OpenAI LLM"""
        monkeypatch.setenv("OPENAI_API_KEY", "test_key")
        mock_is_available.return_value = True
        mock_get_provider.return_value = "OpenAI"

        llm = LLMProvider.create_llm("gpt-5-mini", temperature=0.5, max_tokens=500, streaming=True)

        mock_openai.assert_called_once()
        call_kwargs = mock_openai.call_args[1]
        assert call_kwargs["model"] == "gpt-5-mini"
        assert call_kwargs["temperature"] == 0.5
        assert call_kwargs["max_tokens"] == 500
        assert call_kwargs["streaming"] is True

    @patch("app.services.llm.provider.ModelRegistry.is_model_available")
    @patch("app.services.llm.provider.ModelRegistry.get_provider")
    @patch("app.services.llm.provider.ModelRegistry.get_env_key")
    @patch("app.services.llm.provider.ModelRegistry._get_api_key")
    @patch("app.services.llm.provider.ChatAnthropic")
    def test_create_anthropic_llm(
        self,
        mock_anthropic,
        mock_get_api_key,
        mock_get_env_key,
        mock_get_provider,
        mock_is_available,
        monkeypatch,
    ):
        """Test creating Anthropic LLM"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key")
        mock_is_available.return_value = True
        mock_get_provider.return_value = "Anthropic"
        mock_get_env_key.return_value = "ANTHROPIC_API_KEY"
        mock_get_api_key.return_value = "test_key"

        llm = LLMProvider.create_llm("claude-haiku-4-5")

        mock_anthropic.assert_called_once()

    @patch("app.services.llm.provider.ModelRegistry.is_model_available")
    @patch("app.services.llm.provider.ModelRegistry.get_provider")
    @patch("app.services.llm.provider.ChatGoogleGenerativeAI")
    def test_create_google_llm(
        self, mock_google, mock_get_provider, mock_is_available, monkeypatch
    ):
        """Test creating Google LLM"""
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")
        mock_is_available.return_value = True
        mock_get_provider.return_value = "Google"

        llm = LLMProvider.create_llm("gemini-3-flash-preview")

        mock_google.assert_called_once()

    @patch("app.services.llm.provider.ModelRegistry.is_model_available")
    @patch("app.services.llm.provider.ModelRegistry.get_provider")
    @patch("app.services.llm.provider.ModelRegistry.get_env_key")
    @patch("app.services.llm.provider.ModelRegistry._get_api_key")
    @patch("app.services.llm.provider.ChatHuggingFace")
    @patch("app.services.llm.provider.HuggingFaceEndpoint")
    def test_create_huggingface_llm(
        self,
        mock_hf,
        mock_chat_hf,
        mock_get_api_key,
        mock_get_env_key,
        mock_get_provider,
        mock_is_available,
        monkeypatch,
    ):
        """Test creating HuggingFace LLM"""
        monkeypatch.setenv("HF_API_KEY", "test_key")
        mock_is_available.return_value = True
        mock_get_provider.return_value = "HuggingFace"
        mock_get_env_key.return_value = "HF_API_KEY"
        mock_get_api_key.return_value = "test_key"

        llm = LLMProvider.create_llm("mistralai/Mixtral-8x7B-Instruct-v0.1")

        mock_hf.assert_called_once()
        mock_chat_hf.assert_called_once()

    @patch("app.services.llm.provider.ModelRegistry.is_model_available")
    @patch("app.services.llm.provider.ModelRegistry.get_provider")
    @patch("app.services.llm.provider.ModelRegistry.get_env_key")
    @patch("app.services.llm.provider.ModelRegistry._get_api_key")
    def test_create_llm_unknown_provider(
        self, mock_get_api_key, mock_get_env_key, mock_get_provider, mock_is_available
    ):
        """Test creating LLM with unknown provider raises error"""
        mock_is_available.return_value = True
        mock_get_provider.return_value = "UnknownProvider"
        mock_get_env_key.return_value = "UNKNOWN_API_KEY"
        mock_get_api_key.return_value = "test_key"

        with pytest.raises(ValueError) as exc:
            LLMProvider.create_llm("unknown-model")

        assert "Unknown provider" in str(exc.value)

    def test_format_messages_user(self):
        """Test formatting user message"""
        messages = [{"role": "user", "content": "Hello"}]
        formatted = LLMProvider.format_messages(messages)

        assert len(formatted) == 1
        assert formatted[0].content == "Hello"
        assert formatted[0].__class__.__name__ == "HumanMessage"

    def test_format_messages_assistant(self):
        """Test formatting assistant message"""
        messages = [{"role": "assistant", "content": "Hi there"}]
        formatted = LLMProvider.format_messages(messages)

        assert len(formatted) == 1
        assert formatted[0].content == "Hi there"
        assert formatted[0].__class__.__name__ == "AIMessage"

    def test_format_messages_system(self):
        """Test formatting system message"""
        messages = [{"role": "system", "content": "You are a helpful assistant"}]
        formatted = LLMProvider.format_messages(messages)

        assert len(formatted) == 1
        assert formatted[0].content == "You are a helpful assistant"
        assert formatted[0].__class__.__name__ == "SystemMessage"

    def test_format_messages_conversation(self):
        """Test formatting multi-turn conversation"""
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "How are you?"},
        ]
        formatted = LLMProvider.format_messages(messages)

        assert len(formatted) == 4
        assert formatted[0].__class__.__name__ == "SystemMessage"
        assert formatted[1].__class__.__name__ == "HumanMessage"
        assert formatted[2].__class__.__name__ == "AIMessage"
        assert formatted[3].__class__.__name__ == "HumanMessage"

    def test_format_messages_with_message_objects(self):
        """Test formatting Message objects"""
        messages = [
            Message(role="user", content="Test"),
            Message(role="assistant", content="Response"),
        ]
        formatted = LLMProvider.format_messages(messages)

        assert len(formatted) == 2
        assert formatted[0].content == "Test"
        assert formatted[1].content == "Response"

    def test_format_messages_empty(self):
        """Test formatting empty message list"""
        formatted = LLMProvider.format_messages([])
        assert formatted == []

    @pytest.mark.asyncio
    async def test_stream_llm_response_basic(self):
        """Test streaming LLM response with content attribute"""

        class MockChunk:
            def __init__(self, content):
                self.content = content

        async def mock_stream(messages):
            yield MockChunk("Hello")
            yield MockChunk(" ")
            yield MockChunk("World")

        mock_llm = Mock()
        mock_llm.astream = mock_stream

        result = []
        async for chunk in LLMProvider.stream_llm_response(mock_llm, []):
            result.append(chunk)

        assert result == ["Hello", " ", "World"]

    @pytest.mark.asyncio
    async def test_stream_llm_response_without_content(self):
        """Test streaming LLM response without content attribute"""

        async def mock_stream(messages):
            yield "Chunk1"
            yield "Chunk2"

        mock_llm = Mock()
        mock_llm.astream = mock_stream

        result = []
        async for chunk in LLMProvider.stream_llm_response(mock_llm, []):
            result.append(chunk)

        assert result == ["Chunk1", "Chunk2"]

    def test_create_llm_default_parameters(self):
        """Test that create_llm uses default parameters correctly"""
        with patch("app.services.llm.provider.ModelRegistry.is_model_available", return_value=True):
            with patch(
                "app.services.llm.provider.ModelRegistry.get_provider", return_value="OpenAI"
            ):
                with patch("app.services.llm.provider.ChatOpenAI") as mock_openai:
                    LLMProvider.create_llm("gpt-5-mini")

                    call_kwargs = mock_openai.call_args[1]
                    assert call_kwargs["temperature"] == 0.7
                    assert call_kwargs["max_tokens"] == 1024
                    assert call_kwargs["streaming"] is True
