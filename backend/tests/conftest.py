"""
Pytest fixtures for backend tests
"""
import os
import tempfile
import pytest
from fastapi.testclient import TestClient

# Set test environment before importing app
os.environ["CHROMA_DB_PATH"] = tempfile.mkdtemp()
os.environ["UPLOADS_PATH"] = tempfile.mkdtemp()
os.environ["SESSIONS_PATH"] = tempfile.mkdtemp()
os.environ["DEFAULT_HF_API_KEY"] = "test_hf_key_default"

from app.main import app


@pytest.fixture
def client():
    """Create test client"""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def sample_text_file(tmp_path):
    """Create a sample text file for testing"""
    file_path = tmp_path / "test_document.txt"
    file_path.write_text("This is a test document.\n\nIt has multiple paragraphs.\n\nUsed for testing RAG functionality.")
    return file_path
