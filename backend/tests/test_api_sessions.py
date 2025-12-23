"""
Tests for /api/sessions endpoints
"""
import pytest


def test_create_session(client):
    """Test creating a new session"""
    response = client.post(
        "/api/sessions",
        json={"model_id": "mistralai/Mixtral-8x7B-Instruct-v0.1"}
    )
    assert response.status_code == 200

    data = response.json()
    assert "session_id" in data
    assert data["session_id"]


def test_get_sessions(client):
    """Test listing sessions"""
    # Create a session first
    client.post(
        "/api/sessions",
        json={"model_id": "mistralai/Mixtral-8x7B-Instruct-v0.1"}
    )

    response = client.get("/api/sessions")
    assert response.status_code == 200

    data = response.json()
    assert "sessions" in data
    assert isinstance(data["sessions"], list)


def test_get_session_by_id(client):
    """Test getting a specific session"""
    # Create a session
    create_response = client.post(
        "/api/sessions",
        json={"model_id": "mistralai/Mixtral-8x7B-Instruct-v0.1"}
    )
    session_id = create_response.json()["session_id"]

    # Get the session
    response = client.get(f"/api/sessions/{session_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == session_id
    assert "messages" in data
    assert "created_at" in data


def test_get_nonexistent_session(client):
    """Test getting a session that doesn't exist"""
    response = client.get("/api/sessions/nonexistent-id")
    assert response.status_code == 404


def test_delete_session(client):
    """Test deleting a session"""
    # Create a session
    create_response = client.post(
        "/api/sessions",
        json={"model_id": "mistralai/Mixtral-8x7B-Instruct-v0.1"}
    )
    session_id = create_response.json()["session_id"]

    # Delete it
    response = client.delete(f"/api/sessions/{session_id}")
    assert response.status_code == 200

    # Verify it's gone
    get_response = client.get(f"/api/sessions/{session_id}")
    assert get_response.status_code == 404
