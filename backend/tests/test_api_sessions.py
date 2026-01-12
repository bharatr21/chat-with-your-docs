"""
Tests for /api/sessions endpoints
"""


def test_create_session(client):
    """Test creating a new session"""
    response = client.post(
        "/api/sessions", json={"model_id": "mistralai/Mixtral-8x7B-Instruct-v0.1"}
    )
    assert response.status_code == 200

    data = response.json()
    assert "id" in data
    assert data["id"]


def test_get_sessions(client):
    """Test listing sessions"""
    # Create a session first
    client.post("/api/sessions", json={"model_id": "mistralai/Mixtral-8x7B-Instruct-v0.1"})

    response = client.get("/api/sessions")
    assert response.status_code == 200

    data = response.json()
    assert "sessions" in data
    assert isinstance(data["sessions"], list)


def test_get_session_by_id(client):
    """Test getting a specific session"""
    # Create a session
    create_response = client.post(
        "/api/sessions", json={"model_id": "mistralai/Mixtral-8x7B-Instruct-v0.1"}
    )
    session_id = create_response.json()["id"]

    # Get the session
    response = client.get(f"/api/sessions/{session_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == session_id
    assert "messages" in data
    assert "created_at" in data


def test_get_nonexistent_session(client):
    """Test getting a session that doesn't exist"""
    # Use a valid UUID format for non-existent session
    nonexistent_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/sessions/{nonexistent_id}")
    assert response.status_code == 404


def test_delete_session(client):
    """Test deleting a session"""
    # Create a session
    create_response = client.post(
        "/api/sessions", json={"model_id": "mistralai/Mixtral-8x7B-Instruct-v0.1"}
    )
    session_id = create_response.json()["id"]

    # Delete it
    response = client.delete(f"/api/sessions/{session_id}")
    assert response.status_code == 200

    # Verify it's gone
    get_response = client.get(f"/api/sessions/{session_id}")
    assert get_response.status_code == 404


def test_path_traversal_protection(client):
    """Test that path traversal attacks are rejected at API level"""
    # Test various path traversal attempts
    # Note: Some may be blocked by FastAPI routing (404) before reaching our validation
    # But we test that our validation works when the request does reach us

    malicious_ids = [
        ("..%2F..%2Fetc%2Fpasswd", True),  # URL-encoded ../
        ("..\\..\\windows\\system32", True),  # Backslashes (Windows-style)
        ("not-a-uuid", True),  # Invalid UUID format
    ]

    for malicious_id, should_validate in malicious_ids:
        # GET endpoint should reject with 400 (validation error) or 404 (routing)
        response = client.get(f"/api/sessions/{malicious_id}")
        # Either our validation catches it (400) or FastAPI routing blocks it (404)
        assert response.status_code in [400, 404]
        if response.status_code == 400:
            assert "Invalid session ID" in response.json()["detail"]

        # DELETE endpoint should reject
        response = client.delete(f"/api/sessions/{malicious_id}")
        assert response.status_code in [400, 404]
        if response.status_code == 400:
            assert "Invalid session ID" in response.json()["detail"]


def test_create_session_with_invalid_model_id(client):
    """Test creating a session with an invalid model_id"""
    response = client.post(
        "/api/sessions", json={"model_id": "invalid-model-id"}
    )
    assert response.status_code == 400
    assert "Invalid model_id" in response.json()["detail"]
    assert "not found in registry" in response.json()["detail"]


def test_create_session_with_invalid_document_id(client):
    """Test creating a session with invalid document_ids"""
    response = client.post(
        "/api/sessions",
        json={
            "model_id": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "document_ids": ["nonexistent-doc-id"]
        }
    )
    assert response.status_code == 400
    assert "Invalid document_id" in response.json()["detail"]
    assert "Document not found" in response.json()["detail"]


def test_create_session_with_mixed_document_ids(client):
    """Test creating a session with some valid and some invalid document_ids"""
    # Upload a document first
    upload_response = client.post(
        "/api/documents/upload",
        files={"file": ("test.txt", b"Test content", "text/plain")}
    )
    assert upload_response.status_code == 200
    valid_doc_id = upload_response.json()["id"]

    # Try to create session with mix of valid and invalid document_ids
    response = client.post(
        "/api/sessions",
        json={
            "model_id": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "document_ids": [valid_doc_id, "nonexistent-doc-id"]
        }
    )
    assert response.status_code == 400
    assert "Invalid document_id" in response.json()["detail"]
    assert "nonexistent-doc-id" in response.json()["detail"]


def test_create_session_with_multiple_invalid_document_ids(client):
    """Test creating a session with multiple invalid document_ids returns all at once"""
    response = client.post(
        "/api/sessions",
        json={
            "model_id": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "document_ids": ["invalid-id-1", "invalid-id-2", "invalid-id-3"]
        }
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    # Should list all invalid IDs
    assert "Invalid document_ids" in detail  # Plural form
    assert "invalid-id-1" in detail
    assert "invalid-id-2" in detail
    assert "invalid-id-3" in detail
    assert "3 documents not found" in detail
