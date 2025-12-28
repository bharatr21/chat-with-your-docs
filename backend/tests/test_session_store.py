"""
Tests for session file store
"""
import pytest
import os
import tempfile
from datetime import datetime
from app.services.session.file_store import SessionStore
from app.models.schemas import Message


@pytest.fixture
def temp_session_dir():
    """Create temporary session directory"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def session_store(temp_session_dir):
    """Create SessionStore with temporary directory"""
    return SessionStore(session_dir=temp_session_dir)


def test_create_session(session_store):
    """Test creating a new session"""
    session = session_store.create_session(
        model_id="test-model",
        document_ids=["doc1", "doc2"],
        name="Test Session"
    )
    
    assert session.id is not None
    assert session.name == "Test Session"
    assert session.model_id == "test-model"
    assert session.document_ids == ["doc1", "doc2"]
    assert session.messages == []
    assert isinstance(session.created_at, datetime)
    assert isinstance(session.updated_at, datetime)


def test_create_session_without_name(session_store):
    """Test creating session without name"""
    session = session_store.create_session(
        model_id="test-model",
        document_ids=[]
    )
    
    assert session.name is None
    assert session.model_id == "test-model"
    assert session.document_ids == []


def test_get_session(session_store):
    """Test getting session by ID"""
    # Create session
    created = session_store.create_session(
        model_id="test-model",
        document_ids=["doc1"]
    )
    
    # Retrieve session
    retrieved = session_store.get_session(created.id)
    
    assert retrieved.id == created.id
    assert retrieved.model_id == created.model_id
    assert retrieved.document_ids == created.document_ids


def test_get_session_not_found(session_store):
    """Test getting non-existent session raises error"""
    with pytest.raises(FileNotFoundError):
        session_store.get_session("nonexistent-id")


def test_update_session_messages(session_store):
    """Test updating session messages"""
    session = session_store.create_session(
        model_id="test-model",
        document_ids=[]
    )
    
    messages = [
        Message(role="user", content="Hello"),
        Message(role="assistant", content="Hi there!")
    ]
    
    session_store.update_session(session.id, messages=messages)
    
    updated = session_store.get_session(session.id)
    assert len(updated.messages) == 2
    assert updated.messages[0].role == "user"
    assert updated.messages[0].content == "Hello"


def test_update_session_model_id(session_store):
    """Test updating session model ID"""
    session = session_store.create_session(
        model_id="old-model",
        document_ids=[]
    )
    
    session_store.update_session(session.id, model_id="new-model")
    
    updated = session_store.get_session(session.id)
    assert updated.model_id == "new-model"


def test_update_session_document_ids(session_store):
    """Test updating session document IDs"""
    session = session_store.create_session(
        model_id="test-model",
        document_ids=["doc1"]
    )
    
    session_store.update_session(session.id, document_ids=["doc2", "doc3"])
    
    updated = session_store.get_session(session.id)
    assert updated.document_ids == ["doc2", "doc3"]


def test_update_session_name(session_store):
    """Test updating session name"""
    session = session_store.create_session(
        model_id="test-model",
        document_ids=[],
        name="Old Name"
    )
    
    session_store.update_session(session.id, name="New Name")
    
    updated = session_store.get_session(session.id)
    assert updated.name == "New Name"


def test_update_session_updates_timestamp(session_store):
    """Test that updating session updates timestamp"""
    session = session_store.create_session(
        model_id="test-model",
        document_ids=[]
    )
    
    original_updated_at = session.updated_at
    
    # Update session
    session_store.update_session(session.id, name="Updated")
    
    updated = session_store.get_session(session.id)
    assert updated.updated_at > original_updated_at


def test_delete_session(session_store, temp_session_dir):
    """Test deleting a session"""
    session = session_store.create_session(
        model_id="test-model",
        document_ids=[]
    )
    
    # Verify file exists
    session_path = os.path.join(temp_session_dir, f"{session.id}.json")
    assert os.path.exists(session_path)
    
    # Delete session
    session_store.delete_session(session.id)
    
    # Verify file deleted
    assert not os.path.exists(session_path)


def test_delete_session_nonexistent(session_store):
    """Test deleting non-existent session doesn't raise error"""
    # Should not raise
    session_store.delete_session("nonexistent-id")


def test_list_sessions_empty(session_store):
    """Test listing sessions when empty"""
    sessions = session_store.list_sessions()
    assert sessions == []


def test_list_sessions_single(session_store):
    """Test listing single session"""
    session = session_store.create_session(
        model_id="test-model",
        document_ids=[]
    )
    
    sessions = session_store.list_sessions()
    assert len(sessions) == 1
    assert sessions[0].id == session.id


def test_list_sessions_multiple(session_store):
    """Test listing multiple sessions"""
    s1 = session_store.create_session(model_id="model1", document_ids=[])
    s2 = session_store.create_session(model_id="model2", document_ids=[])
    s3 = session_store.create_session(model_id="model3", document_ids=[])
    
    sessions = session_store.list_sessions()
    assert len(sessions) == 3
    
    session_ids = {s.id for s in sessions}
    assert session_ids == {s1.id, s2.id, s3.id}


def test_list_sessions_sorted_by_updated_at(session_store):
    """Test that sessions are sorted by most recent first"""
    import time
    
    s1 = session_store.create_session(model_id="model1", document_ids=[])
    time.sleep(0.01)
    s2 = session_store.create_session(model_id="model2", document_ids=[])
    time.sleep(0.01)
    
    # Update s1 to make it most recent
    session_store.update_session(s1.id, name="Updated")
    
    sessions = session_store.list_sessions()
    
    # s1 should be first (most recent)
    assert sessions[0].id == s1.id
    assert sessions[1].id == s2.id


def test_add_message(session_store):
    """Test adding message to session"""
    session = session_store.create_session(
        model_id="test-model",
        document_ids=[]
    )
    
    message = Message(role="user", content="Hello")
    session_store.add_message(session.id, message)
    
    updated = session_store.get_session(session.id)
    assert len(updated.messages) == 1
    assert updated.messages[0].content == "Hello"


def test_add_multiple_messages(session_store):
    """Test adding multiple messages to session"""
    session = session_store.create_session(
        model_id="test-model",
        document_ids=[]
    )
    
    session_store.add_message(session.id, Message(role="user", content="Hi"))
    session_store.add_message(session.id, Message(role="assistant", content="Hello"))
    session_store.add_message(session.id, Message(role="user", content="How are you?"))
    
    updated = session_store.get_session(session.id)
    assert len(updated.messages) == 3
    assert updated.messages[0].content == "Hi"
    assert updated.messages[1].content == "Hello"
    assert updated.messages[2].content == "How are you?"


def test_add_message_updates_timestamp(session_store):
    """Test that adding message updates session timestamp"""
    session = session_store.create_session(
        model_id="test-model",
        document_ids=[]
    )
    
    original_updated_at = session.updated_at
    
    session_store.add_message(session.id, Message(role="user", content="Test"))
    
    updated = session_store.get_session(session.id)
    assert updated.updated_at > original_updated_at


def test_session_exists_true(session_store):
    """Test session_exists returns True for existing session"""
    session = session_store.create_session(
        model_id="test-model",
        document_ids=[]
    )
    
    assert session_store.session_exists(session.id) is True


def test_session_exists_false(session_store):
    """Test session_exists returns False for non-existent session"""
    assert session_store.session_exists("nonexistent-id") is False


def test_session_with_empty_document_ids(session_store):
    """Test session with empty document list"""
    session = session_store.create_session(
        model_id="test-model",
        document_ids=[]
    )
    
    assert session.document_ids == []


def test_session_with_multiple_document_ids(session_store):
    """Test session with multiple documents"""
    doc_ids = ["doc1", "doc2", "doc3", "doc4"]
    session = session_store.create_session(
        model_id="test-model",
        document_ids=doc_ids
    )
    
    assert session.document_ids == doc_ids


def test_session_message_timestamps(session_store):
    """Test that messages have timestamps"""
    session = session_store.create_session(
        model_id="test-model",
        document_ids=[]
    )
    
    message = Message(role="user", content="Test")
    session_store.add_message(session.id, message)
    
    updated = session_store.get_session(session.id)
    assert updated.messages[0].timestamp is not None


def test_list_sessions_ignores_corrupted_files(session_store, temp_session_dir):
    """Test that list_sessions skips corrupted session files"""
    # Create valid session
    session = session_store.create_session(
        model_id="test-model",
        document_ids=[]
    )
    
    # Create corrupted session file
    corrupted_path = os.path.join(temp_session_dir, "corrupted.json")
    with open(corrupted_path, 'w') as f:
        f.write("{ invalid json }")
    
    # Should only return valid session
    sessions = session_store.list_sessions()
    assert len(sessions) == 1
    assert sessions[0].id == session.id