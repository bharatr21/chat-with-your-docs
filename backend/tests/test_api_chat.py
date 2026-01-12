"""
Tests for chat API endpoints
"""

from unittest.mock import Mock, patch

import pytest


class TestChatAPI:
    """Test chat API endpoints"""

    @pytest.mark.asyncio
    async def test_chat_endpoint_basic(self, client, monkeypatch):
        """Test basic chat request"""
        monkeypatch.setenv("HF_API_KEY", "test_key")

        with patch("app.api.routes.chat.RAGPipeline") as mock_pipeline_class:
            mock_pipeline = Mock()

            async def mock_run(*args, **kwargs):
                yield "Test"
                yield " response"

            mock_pipeline.run = mock_run
            mock_pipeline_class.return_value = mock_pipeline

            response = client.post(
                "/api/chat",
                json={
                    "messages": [{"role": "user", "content": "Hello"}],
                    "model_id": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                    "stream": False,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert "message" in data

    def test_chat_missing_messages(self, client):
        """Test chat with missing messages"""
        response = client.post("/api/chat", json={"model_id": "test-model", "messages": []})

        assert response.status_code == 400
        assert "No messages" in response.json()["detail"]

    def test_chat_last_message_not_user(self, client):
        """Test chat when last message is not from user"""
        response = client.post(
            "/api/chat",
            json={
                "messages": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi"},
                ],
                "model_id": "test-model",
            },
        )

        assert response.status_code == 400
        assert "must be from user" in response.json()["detail"]

    def test_chat_unavailable_model_fallback(self, client, monkeypatch):
        """Test chat falls back to default model when requested model unavailable"""
        monkeypatch.setenv("HF_API_KEY", "test_key")

        with patch("app.api.routes.chat.ModelRegistry.is_model_available", return_value=False):
            with patch(
                "app.api.routes.chat.ModelRegistry.get_default_model", return_value="default-model"
            ):
                with patch("app.api.routes.chat.RAGPipeline") as mock_pipeline_class:
                    mock_pipeline = Mock()

                    async def mock_run(*args, **kwargs):
                        yield "Response"

                    mock_pipeline.run = mock_run
                    mock_pipeline_class.return_value = mock_pipeline

                    response = client.post(
                        "/api/chat",
                        json={
                            "messages": [{"role": "user", "content": "Test"}],
                            "model_id": "unavailable-model",
                            "stream": False,
                        },
                    )

                    # Should succeed with fallback
                    assert response.status_code == 200

    def test_chat_no_available_models(self, client, monkeypatch):
        """Test chat when no models are available"""
        monkeypatch.setenv("HF_API_KEY", "")
        monkeypatch.setenv("DEFAULT_HF_API_KEY", "")

        with patch("app.api.routes.chat.ModelRegistry.is_model_available", return_value=False):
            with patch("app.api.routes.chat.ModelRegistry.get_default_model", return_value=None):
                response = client.post(
                    "/api/chat",
                    json={
                        "messages": [{"role": "user", "content": "Test"}],
                        "model_id": "test-model",
                    },
                )

                assert response.status_code == 400
                assert "No available models" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_chat_with_document_ids(self, client, monkeypatch):
        """Test chat with specific document IDs"""
        monkeypatch.setenv("HF_API_KEY", "test_key")

        with patch("app.api.routes.chat.RAGPipeline") as mock_pipeline_class:
            mock_pipeline = Mock()

            async def mock_run(*args, **kwargs):
                yield "Response"

            mock_pipeline.run = mock_run
            mock_pipeline_class.return_value = mock_pipeline

            response = client.post(
                "/api/chat",
                json={
                    "messages": [{"role": "user", "content": "Test"}],
                    "model_id": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                    "document_ids": ["doc1", "doc2"],
                    "stream": False,
                },
            )

            assert response.status_code == 200

            # Verify pipeline was created with document IDs
            call_kwargs = mock_pipeline_class.call_args[1]
            assert call_kwargs["document_ids"] == ["doc1", "doc2"]

    @pytest.mark.asyncio
    async def test_chat_with_session(self, client, monkeypatch):
        """Test chat with existing session"""
        monkeypatch.setenv("HF_API_KEY", "test_key")

        with patch("app.api.routes.chat.session_store") as mock_session_store:
            mock_session_store.session_exists.return_value = True
            mock_session_store.get_session.return_value = Mock(messages=[])
            mock_session_store.add_message = Mock()

            with patch("app.api.routes.chat.RAGPipeline") as mock_pipeline_class:
                mock_pipeline = Mock()

                async def mock_run(*args, **kwargs):
                    yield "Response"

                mock_pipeline.run = mock_run
                mock_pipeline_class.return_value = mock_pipeline

                response = client.post(
                    "/api/chat",
                    json={
                        "messages": [{"role": "user", "content": "Test"}],
                        "model_id": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                        "session_id": "test-session",
                        "stream": False,
                    },
                )

                assert response.status_code == 200

                # Verify messages were added to session
                assert mock_session_store.add_message.call_count == 2  # user + assistant

    @pytest.mark.asyncio
    async def test_chat_with_temperature_and_max_tokens(self, client, monkeypatch):
        """Test chat with custom temperature and max_tokens"""
        monkeypatch.setenv("HF_API_KEY", "test_key")

        with patch("app.api.routes.chat.RAGPipeline") as mock_pipeline_class:
            mock_pipeline = Mock()

            async def mock_run(*args, **kwargs):
                yield "Response"

            mock_pipeline.run = mock_run
            mock_pipeline_class.return_value = mock_pipeline

            response = client.post(
                "/api/chat",
                json={
                    "messages": [{"role": "user", "content": "Test"}],
                    "model_id": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                    "temperature": 0.5,
                    "max_tokens": 2048,
                    "stream": False,
                },
            )

            assert response.status_code == 200

            # Verify pipeline was created with custom params
            call_kwargs = mock_pipeline_class.call_args[1]
            assert call_kwargs["temperature"] == 0.5
            assert call_kwargs["max_tokens"] == 2048
