"""
Pytest fixtures for backend tests
"""

import os
import shutil

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_test_dirs(tmp_path_factory):
    """Setup test directories for ChromaDB and sessions"""
    # Create temp directories for test isolation
    chroma_dir = tmp_path_factory.mktemp("chroma")
    session_dir = tmp_path_factory.mktemp("sessions")

    # Set environment variables before app import
    os.environ["CHROMA_DB_PATH"] = str(chroma_dir)
    os.environ["SESSION_DIR"] = str(session_dir)
    os.environ["DEFAULT_HF_API_KEY"] = "test_hf_key_default"

    yield

    # Cleanup after all tests complete
    shutil.rmtree(chroma_dir, ignore_errors=True)
    shutil.rmtree(session_dir, ignore_errors=True)


@pytest.fixture
def client():
    """Create test client"""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def sample_text_file(tmp_path):
    """Create a sample text file for testing"""
    file_path = tmp_path / "test_document.txt"
    file_path.write_text(
        "This is a test document.\n\nIt has multiple paragraphs.\n\nUsed for testing RAG functionality."
    )
    return file_path
