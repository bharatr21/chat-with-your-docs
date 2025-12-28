"""
Tests for document metadata management
"""
import pytest
import json
import os
import tempfile
from datetime import datetime
from app.services.document.metadata import MetadataManager


@pytest.fixture
def temp_metadata_dir():
    """Create temporary metadata directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def metadata_manager(temp_metadata_dir):
    """Create MetadataManager with temporary directory"""
    return MetadataManager(metadata_dir=temp_metadata_dir)


def test_init_creates_directory(temp_metadata_dir):
    """Test that initialization creates metadata directory"""
    subdir = os.path.join(temp_metadata_dir, "metadata")
    manager = MetadataManager(metadata_dir=subdir)
    
    assert os.path.exists(subdir)
    assert os.path.isdir(subdir)


def test_save_metadata(metadata_manager, temp_metadata_dir):
    """Test saving metadata to file"""
    doc_id = "test-doc-123"
    metadata = {
        "filename": "test.pdf",
        "file_type": "application/pdf",
        "file_size": 1024
    }
    
    metadata_manager.save_metadata(doc_id, metadata)
    
    # Check file exists
    metadata_path = os.path.join(temp_metadata_dir, f"{doc_id}.json")
    assert os.path.exists(metadata_path)
    
    # Check contents
    with open(metadata_path, 'r') as f:
        saved = json.load(f)
    
    assert saved["filename"] == "test.pdf"
    assert saved["file_type"] == "application/pdf"
    assert saved["file_size"] == 1024
    assert "upload_date" in saved


def test_save_metadata_adds_timestamp(metadata_manager):
    """Test that save_metadata adds upload_date if not present"""
    doc_id = "test-doc"
    metadata = {"filename": "test.pdf"}
    
    metadata_manager.save_metadata(doc_id, metadata)
    loaded = metadata_manager.load_metadata(doc_id)
    
    assert "upload_date" in loaded
    # Verify it's a valid ISO timestamp
    datetime.fromisoformat(loaded["upload_date"])


def test_save_metadata_preserves_existing_timestamp(metadata_manager):
    """Test that save_metadata preserves existing upload_date"""
    doc_id = "test-doc"
    custom_date = "2024-01-01T12:00:00"
    metadata = {
        "filename": "test.pdf",
        "upload_date": custom_date
    }
    
    metadata_manager.save_metadata(doc_id, metadata)
    loaded = metadata_manager.load_metadata(doc_id)
    
    assert loaded["upload_date"] == custom_date


def test_load_metadata(metadata_manager):
    """Test loading metadata from file"""
    doc_id = "test-doc"
    metadata = {
        "filename": "test.pdf",
        "file_type": "application/pdf",
        "chunk_count": 10
    }
    
    metadata_manager.save_metadata(doc_id, metadata)
    loaded = metadata_manager.load_metadata(doc_id)
    
    assert loaded["filename"] == "test.pdf"
    assert loaded["file_type"] == "application/pdf"
    assert loaded["chunk_count"] == 10


def test_load_metadata_not_found(metadata_manager):
    """Test loading non-existent metadata raises error"""
    with pytest.raises(FileNotFoundError) as exc:
        metadata_manager.load_metadata("nonexistent-doc")
    
    assert "not found" in str(exc.value)


def test_delete_metadata(metadata_manager):
    """Test deleting metadata"""
    doc_id = "test-doc"
    metadata = {"filename": "test.pdf"}
    
    metadata_manager.save_metadata(doc_id, metadata)
    assert metadata_manager.exists(doc_id)
    
    metadata_manager.delete_metadata(doc_id)
    assert not metadata_manager.exists(doc_id)


def test_delete_metadata_nonexistent(metadata_manager):
    """Test deleting non-existent metadata doesn't raise error"""
    # Should not raise
    metadata_manager.delete_metadata("nonexistent-doc")


def test_list_all_metadata_empty(metadata_manager):
    """Test listing metadata when directory is empty"""
    result = metadata_manager.list_all_metadata()
    assert result == []


def test_list_all_metadata_single(metadata_manager):
    """Test listing metadata with single document"""
    doc_id = "test-doc"
    metadata = {"filename": "test.pdf"}
    
    metadata_manager.save_metadata(doc_id, metadata)
    result = metadata_manager.list_all_metadata()
    
    assert len(result) == 1
    assert result[0]["id"] == doc_id
    assert result[0]["filename"] == "test.pdf"


def test_list_all_metadata_multiple(metadata_manager):
    """Test listing metadata with multiple documents"""
    docs = [
        ("doc1", {"filename": "file1.pdf"}),
        ("doc2", {"filename": "file2.docx"}),
        ("doc3", {"filename": "file3.txt"})
    ]
    
    for doc_id, metadata in docs:
        metadata_manager.save_metadata(doc_id, metadata)
    
    result = metadata_manager.list_all_metadata()
    
    assert len(result) == 3
    filenames = {item["filename"] for item in result}
    assert filenames == {"file1.pdf", "file2.docx", "file3.txt"}


def test_list_all_metadata_includes_id(metadata_manager):
    """Test that list_all_metadata adds document ID to each entry"""
    doc_id = "test-doc-123"
    metadata = {"filename": "test.pdf"}
    
    metadata_manager.save_metadata(doc_id, metadata)
    result = metadata_manager.list_all_metadata()
    
    assert result[0]["id"] == doc_id


def test_list_all_metadata_corrupted_file(metadata_manager, temp_metadata_dir):
    """Test listing metadata skips corrupted files"""
    # Save valid metadata
    metadata_manager.save_metadata("valid", {"filename": "valid.pdf"})
    
    # Create corrupted JSON file
    corrupted_path = os.path.join(temp_metadata_dir, "corrupted.json")
    with open(corrupted_path, 'w') as f:
        f.write("{ invalid json }")
    
    # Should skip corrupted and return valid
    result = metadata_manager.list_all_metadata()
    assert len(result) == 1
    assert result[0]["id"] == "valid"


def test_exists_true(metadata_manager):
    """Test exists returns True for existing metadata"""
    doc_id = "test-doc"
    metadata = {"filename": "test.pdf"}
    
    metadata_manager.save_metadata(doc_id, metadata)
    assert metadata_manager.exists(doc_id) is True


def test_exists_false(metadata_manager):
    """Test exists returns False for non-existent metadata"""
    assert metadata_manager.exists("nonexistent") is False


def test_metadata_with_complex_data(metadata_manager):
    """Test saving and loading complex metadata structures"""
    doc_id = "complex-doc"
    metadata = {
        "filename": "test.pdf",
        "headers": ["Header 1", "Header 2", "Header 3"],
        "page_count": 10,
        "file_size": 1024000,
        "nested": {
            "key1": "value1",
            "key2": [1, 2, 3]
        }
    }
    
    metadata_manager.save_metadata(doc_id, metadata)
    loaded = metadata_manager.load_metadata(doc_id)
    
    assert loaded["headers"] == ["Header 1", "Header 2", "Header 3"]
    assert loaded["page_count"] == 10
    assert loaded["nested"]["key1"] == "value1"
    assert loaded["nested"]["key2"] == [1, 2, 3]


def test_metadata_special_characters_in_filename(metadata_manager):
    """Test metadata with special characters in filename"""
    doc_id = "test-doc"
    metadata = {
        "filename": "test file (1) [copy].pdf",
        "file_type": "application/pdf"
    }
    
    metadata_manager.save_metadata(doc_id, metadata)
    loaded = metadata_manager.load_metadata(doc_id)
    
    assert loaded["filename"] == "test file (1) [copy].pdf"


def test_metadata_unicode_content(metadata_manager):
    """Test metadata with unicode content"""
    doc_id = "unicode-doc"
    metadata = {
        "filename": "文档.pdf",
        "title": "Документ с русским текстом"
    }
    
    metadata_manager.save_metadata(doc_id, metadata)
    loaded = metadata_manager.load_metadata(doc_id)
    
    assert loaded["filename"] == "文档.pdf"
    assert loaded["title"] == "Документ с русским текстом"


def test_save_metadata_overwrites_existing(metadata_manager):
    """Test that saving metadata overwrites existing file"""
    doc_id = "test-doc"
    
    # Save initial metadata
    metadata_manager.save_metadata(doc_id, {"filename": "old.pdf"})
    
    # Overwrite with new metadata
    metadata_manager.save_metadata(doc_id, {"filename": "new.pdf", "updated": True})
    
    loaded = metadata_manager.load_metadata(doc_id)
    assert loaded["filename"] == "new.pdf"
    assert loaded["updated"] is True


def test_list_all_metadata_nonexistent_directory():
    """Test listing metadata when directory doesn't exist"""
    manager = MetadataManager(metadata_dir="/nonexistent/path")
    result = manager.list_all_metadata()
    assert result == []