"""
Tests for document processor service
"""
import pytest
from app.services.document.processor import DocumentProcessor


@pytest.fixture
def processor():
    return DocumentProcessor()


def test_is_supported_txt(processor):
    """Test that .txt files are supported"""
    assert processor.is_supported("document.txt") is True


def test_is_supported_pdf(processor):
    """Test that .pdf files are supported"""
    assert processor.is_supported("document.pdf") is True


def test_is_supported_docx(processor):
    """Test that .docx files are supported"""
    assert processor.is_supported("document.docx") is True


def test_is_supported_csv(processor):
    """Test that .csv files are supported"""
    assert processor.is_supported("data.csv") is True


def test_is_not_supported(processor):
    """Test that unsupported files are rejected"""
    assert processor.is_supported("file.exe") is False
    assert processor.is_supported("image.jpg") is False
    assert processor.is_supported("archive.zip") is False


def test_extract_text_file(processor, tmp_path):
    """Test extracting text from a text file"""
    file_path = tmp_path / "test.txt"
    content = "Hello, this is a test document.\n\nSecond paragraph."
    file_path.write_text(content)

    text, metadata = processor.extract_text(str(file_path), "test.txt")

    assert text == content
    assert metadata["filename"] == "test.txt"
    assert metadata["file_type"] == "text/plain"
    assert "file_size" in metadata


def test_chunk_text(processor):
    """Test chunking text into smaller pieces"""
    text = "First paragraph.\n\n" * 100  # Create enough text to chunk
    metadata = {"filename": "test.txt"}

    chunks = processor.chunk_text(text, metadata, "doc-123")

    assert len(chunks) >= 1
    assert all(chunk.metadata["doc_id"] == "doc-123" for chunk in chunks)
    assert all("chunk_index" in chunk.metadata for chunk in chunks)


def test_process_document(processor, tmp_path):
    """Test full document processing pipeline"""
    file_path = tmp_path / "test.txt"
    content = "Test content for document processing.\n\n" * 50
    file_path.write_text(content)

    chunks, metadata = processor.process_document(
        str(file_path),
        "test.txt",
        "doc-456"
    )

    assert len(chunks) >= 1
    assert metadata["chunk_count"] == len(chunks)
    assert metadata["filename"] == "test.txt"
