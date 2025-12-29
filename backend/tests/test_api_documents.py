"""
Tests for /api/documents endpoints
"""
import pytest


def test_get_documents_empty(client):
    """Test getting documents when none exist"""
    response = client.get("/api/documents")
    assert response.status_code == 200

    data = response.json()
    assert "documents" in data
    assert isinstance(data["documents"], list)


def test_upload_document(client, sample_text_file):
    """Test uploading a document"""
    with open(sample_text_file, "rb") as f:
        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", f, "text/plain")}
        )

    assert response.status_code == 200

    data = response.json()
    assert "id" in data
    assert "metadata" in data
    assert "chunk_count" in data["metadata"]
    assert data["metadata"]["chunk_count"] > 0


def test_upload_unsupported_file(client, tmp_path):
    """Test uploading an unsupported file type"""
    # Create a fake binary file
    file_path = tmp_path / "test.exe"
    file_path.write_bytes(b"fake executable content")

    with open(file_path, "rb") as f:
        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.exe", f, "application/octet-stream")}
        )

    assert response.status_code == 400


def test_get_document_by_id(client, sample_text_file):
    """Test getting a specific document"""
    # Upload a document first
    with open(sample_text_file, "rb") as f:
        upload_response = client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", f, "text/plain")}
        )
    doc_id = upload_response.json()["id"]

    # Get the document
    response = client.get(f"/api/documents/{doc_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == doc_id
    assert "metadata" in data
    assert "title" in data["metadata"]
    assert "file_type" in data["metadata"]


def test_delete_document(client, sample_text_file):
    """Test deleting a document"""
    # Upload a document
    with open(sample_text_file, "rb") as f:
        upload_response = client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", f, "text/plain")}
        )
    doc_id = upload_response.json()["id"]

    # Delete it
    response = client.delete(f"/api/documents/{doc_id}")
    assert response.status_code == 200

    # Verify it's gone
    get_response = client.get(f"/api/documents/{doc_id}")
    assert get_response.status_code == 404
