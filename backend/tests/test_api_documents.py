"""
Tests for /api/documents endpoints
"""


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
            "/api/documents/upload", files={"file": ("test.txt", f, "text/plain")}
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
            "/api/documents/upload", files={"file": ("test.exe", f, "application/octet-stream")}
        )

    assert response.status_code == 400


def test_get_document_by_id(client, sample_text_file):
    """Test getting a specific document"""
    # Upload a document first
    with open(sample_text_file, "rb") as f:
        upload_response = client.post(
            "/api/documents/upload", files={"file": ("test.txt", f, "text/plain")}
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
            "/api/documents/upload", files={"file": ("test.txt", f, "text/plain")}
        )
    doc_id = upload_response.json()["id"]

    # Delete it
    response = client.delete(f"/api/documents/{doc_id}")
    assert response.status_code == 200

    # Verify it's gone
    get_response = client.get(f"/api/documents/{doc_id}")
    assert get_response.status_code == 404


def test_upload_document_without_filename(client, tmp_path):
    """Test uploading a file without a filename in Content-Disposition"""
    # Create a test file
    file_path = tmp_path / "test.txt"
    file_path.write_text("Test content")

    # Upload with None as filename (simulates missing filename in Content-Disposition)
    with open(file_path, "rb") as f:
        response = client.post(
            "/api/documents/upload", files={"file": (None, f, "text/plain")}
        )

    # FastAPI may return 422 (validation error) or 400 (our custom error)
    # Both are acceptable for invalid input
    assert response.status_code in [400, 422]


def test_upload_document_path_traversal_attack(client, tmp_path):
    """Test that path traversal attacks in filename are prevented"""
    # Create a test file
    file_path = tmp_path / "test.txt"
    file_path.write_text("Test content for path traversal test")

    # Attempt path traversal with various attack vectors
    malicious_filenames = [
        "../../etc/passwd.txt",  # Unix-style path traversal
        "..\\..\\windows\\system32\\config.txt",  # Windows-style path traversal
        "../../../../../../../etc/shadow.txt",  # Deep path traversal
        "....//....//etc/hosts.txt",  # Double encoding attempt
        "/etc/passwd.txt",  # Absolute path
        "C:\\Windows\\System32\\config.txt",  # Windows absolute path
    ]

    for malicious_filename in malicious_filenames:
        with open(file_path, "rb") as f:
            response = client.post(
                "/api/documents/upload",
                files={"file": (malicious_filename, f, "text/plain")}
            )

        # Should either succeed with sanitized filename or fail validation
        # but NOT create files outside uploads directory
        if response.status_code == 200:
            doc_id = response.json()["id"]
            returned_filename = response.json()["filename"]

            # Verify filename doesn't contain path traversal characters
            assert ".." not in returned_filename
            assert "/" not in returned_filename
            assert "\\" not in returned_filename

            # Verify the file was created in the correct location
            import os
            uploads_dir = os.path.abspath("./uploads")

            # Check that file exists with doc_id prefix in uploads directory
            found_file = False
            for filename in os.listdir(uploads_dir):
                if filename.startswith(doc_id):
                    found_file = True
                    full_path = os.path.abspath(os.path.join(uploads_dir, filename))
                    # Verify it's actually in the uploads directory (not outside)
                    assert os.path.commonpath([uploads_dir, full_path]) == uploads_dir

            assert found_file, f"File with doc_id {doc_id} not found in uploads directory"


def test_upload_document_null_byte_in_filename(client, tmp_path):
    """Test that null bytes in filename are handled safely"""
    file_path = tmp_path / "test.txt"
    file_path.write_text("Test content")

    # Filename with null byte (could cause issues in C-based filesystem APIs)
    malicious_filename = "test\x00.txt"

    with open(file_path, "rb") as f:
        response = client.post(
            "/api/documents/upload",
            files={"file": (malicious_filename, f, "text/plain")}
        )

    # Should succeed with null byte removed
    if response.status_code == 200:
        returned_filename = response.json()["filename"]
        assert "\x00" not in returned_filename


def test_upload_document_special_characters_in_filename(client, tmp_path):
    """Test that special characters in filename are handled safely"""
    file_path = tmp_path / "test.txt"
    file_path.write_text("Test content")

    # Filename with various special characters
    filename_with_special_chars = "test<>:|?*.txt"

    with open(file_path, "rb") as f:
        response = client.post(
            "/api/documents/upload",
            files={"file": (filename_with_special_chars, f, "text/plain")}
        )

    # Should succeed with special characters sanitized
    if response.status_code == 200:
        returned_filename = response.json()["filename"]
        # Special characters should be replaced or removed
        dangerous_chars = ['<', '>', ':', '|', '?', '*']
        for char in dangerous_chars:
            assert char not in returned_filename
