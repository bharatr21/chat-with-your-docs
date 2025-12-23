"""
Tests for /api/models endpoint
"""


def test_get_models(client):
    """Test getting available models"""
    response = client.get("/api/models")
    assert response.status_code == 200

    data = response.json()
    assert "models" in data
    assert isinstance(data["models"], list)

    # Should have at least one model (HuggingFace default)
    assert len(data["models"]) >= 1

    # Check model structure
    for model in data["models"]:
        assert "id" in model
        assert "name" in model
        assert "provider" in model
        assert "available" in model


def test_models_have_required_fields(client):
    """Test that all models have required fields"""
    response = client.get("/api/models")
    data = response.json()

    for model in data["models"]:
        assert model["id"], "Model ID should not be empty"
        assert model["name"], "Model name should not be empty"
        assert model["provider"] in ["HuggingFace", "OpenAI", "Anthropic", "Google"]
