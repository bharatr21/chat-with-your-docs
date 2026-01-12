"""
Tests for streaming utilities
"""

import json

import pytest

from app.core.streaming import StreamBuffer, VercelStreamFormatter


async def async_iter(items):
    """Helper to create async iterator"""
    for item in items:
        yield item


@pytest.mark.asyncio
async def test_format_stream_basic():
    """Test basic stream formatting"""
    chunks = ["Hello", " ", "World"]

    result = []
    async for formatted in VercelStreamFormatter.format_stream(async_iter(chunks)):
        result.append(formatted)

    # Should have 3 text-delta events + 1 DONE
    assert len(result) == 4

    # Check text-delta events
    for i in range(3):
        assert result[i].startswith("data: ")
        data = json.loads(result[i][6:])
        assert data["type"] == "text-delta"
        assert "id" in data
        assert data["delta"] == chunks[i]

    # Check DONE marker
    assert result[3] == "data: [DONE]\n\n"


@pytest.mark.asyncio
async def test_format_stream_with_message_id():
    """Test stream formatting with custom message ID"""
    chunks = ["test"]
    message_id = "test-message-123"

    result = []
    async for formatted in VercelStreamFormatter.format_stream(
        async_iter(chunks), message_id=message_id
    ):
        result.append(formatted)

    # Check message ID is used
    data = json.loads(result[0][6:])
    assert data["id"] == message_id


@pytest.mark.asyncio
async def test_format_stream_empty_chunks():
    """Test stream formatting filters out empty chunks"""
    chunks = ["Hello", "", "World", None, "!"]

    result = []
    async for formatted in VercelStreamFormatter.format_stream(async_iter(chunks)):
        result.append(formatted)

    # Should only have non-empty chunks + DONE
    # Empty string and None should be filtered
    text_deltas = [r for r in result if "text-delta" in r]
    assert len(text_deltas) == 3  # "Hello", "World", "!"


@pytest.mark.asyncio
async def test_format_stream_error_handling():
    """Test stream formatting handles errors and always sends [DONE]"""

    async def error_iter():
        yield "chunk1"
        raise ValueError("Test error")

    result = []
    async for formatted in VercelStreamFormatter.format_stream(error_iter()):
        result.append(formatted)

    # Should have 1 text-delta + 1 error event + 1 DONE marker
    assert len(result) == 3

    # Check text-delta event
    data0 = json.loads(result[0][6:])
    assert data0["type"] == "text-delta"
    assert data0["delta"] == "chunk1"

    # Check error event
    assert "error" in result[1]
    data1 = json.loads(result[1][6:])
    assert data1["type"] == "error"
    assert "Test error" in data1["error"]

    # Check DONE marker is sent even after error
    assert result[2] == "data: [DONE]\n\n"


@pytest.mark.asyncio
async def test_format_stream_maintains_order():
    """Test stream formatting maintains chunk order"""
    chunks = ["First", "Second", "Third", "Fourth", "Fifth"]

    result = []
    async for formatted in VercelStreamFormatter.format_stream(async_iter(chunks)):
        if "text-delta" in formatted:
            data = json.loads(formatted[6:])
            result.append(data["delta"])

    assert result == chunks


def test_format_sources():
    """Test formatting source metadata"""
    sources = [{"filename": "doc1.pdf", "page": 1}, {"filename": "doc2.pdf", "page": 5}]
    message_id = "test-id"

    formatted = VercelStreamFormatter.format_sources(sources, message_id)

    assert formatted.startswith("data: ")
    data = json.loads(formatted[6:])

    assert data["type"] == "metadata"
    assert data["id"] == message_id
    assert data["metadata"]["sources"] == sources


def test_format_sources_empty():
    """Test formatting empty sources"""
    sources = []
    message_id = "test-id"

    formatted = VercelStreamFormatter.format_sources(sources, message_id)
    data = json.loads(formatted[6:])

    assert data["metadata"]["sources"] == []


@pytest.mark.asyncio
async def test_stream_buffer_basic():
    """Test StreamBuffer basic functionality"""
    chunks = ["Hello", " ", "World"]
    buffer = StreamBuffer()

    result = []
    async for chunk in buffer.stream_chunks(async_iter(chunks)):
        result.append(chunk)

    assert result == chunks
    assert buffer.get_full_response() == "Hello World"


@pytest.mark.asyncio
async def test_stream_buffer_empty():
    """Test StreamBuffer with empty stream"""
    buffer = StreamBuffer()

    result = []
    async for chunk in buffer.stream_chunks(async_iter([])):
        result.append(chunk)

    assert result == []
    assert buffer.get_full_response() == ""


@pytest.mark.asyncio
async def test_stream_buffer_multiple_calls():
    """Test StreamBuffer accumulates across multiple streams"""
    buffer = StreamBuffer()

    # First stream
    async for _ in buffer.stream_chunks(async_iter(["Hello"])):
        pass

    # Second stream (new buffer instance needed)
    buffer2 = StreamBuffer()
    async for _ in buffer2.stream_chunks(async_iter([" World"])):
        pass

    assert buffer.get_full_response() == "Hello"
    assert buffer2.get_full_response() == " World"


@pytest.mark.asyncio
async def test_stream_buffer_special_characters():
    """Test StreamBuffer handles special characters"""
    chunks = ["Hello\n", "World\t", "Test\r\n"]
    buffer = StreamBuffer()

    async for _ in buffer.stream_chunks(async_iter(chunks)):
        pass

    assert buffer.get_full_response() == "Hello\nWorld\tTest\r\n"


@pytest.mark.asyncio
async def test_stream_buffer_unicode():
    """Test StreamBuffer handles unicode characters"""
    chunks = ["Hello ", "🌍", " World"]
    buffer = StreamBuffer()

    async for _ in buffer.stream_chunks(async_iter(chunks)):
        pass

    assert buffer.get_full_response() == "Hello 🌍 World"


@pytest.mark.asyncio
async def test_format_stream_json_serialization():
    """Test that formatted stream produces valid JSON"""
    chunks = ["test", "data"]

    async for formatted in VercelStreamFormatter.format_stream(async_iter(chunks)):
        if formatted.startswith("data: ") and formatted != "data: [DONE]\n\n":
            # Should be valid JSON
            json_str = formatted[6:].strip()
            data = json.loads(json_str)
            assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_format_stream_with_long_chunks():
    """Test stream formatting with long text chunks"""
    long_chunk = "A" * 10000
    chunks = [long_chunk]

    result = []
    async for formatted in VercelStreamFormatter.format_stream(async_iter(chunks)):
        result.append(formatted)

    # Should handle long chunks
    assert len(result) == 2  # 1 text-delta + DONE
    data = json.loads(result[0][6:])
    assert len(data["delta"]) == 10000
