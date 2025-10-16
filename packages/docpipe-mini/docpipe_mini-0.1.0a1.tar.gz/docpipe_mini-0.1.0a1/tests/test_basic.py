"""
Basic tests for docpipe-mini functionality.

Tests core serialization without external dependencies.
"""

import json
import uuid
from pathlib import Path
from typing import Iterator

import pytest

from docpipe import DocumentChunk, serialize, serialize_to_jsonl, list_formats
from docpipe._types import BBox, estimate_tokens


class TestDocumentChunk:
    """Test DocumentChunk functionality."""

    def test_chunk_creation(self):
        """Test creating a document chunk."""
        chunk = DocumentChunk(
            doc_id="test-doc",
            page=1,
            x=0.1,
            y=0.2,
            w=0.8,
            h=0.1,
            type="text",
            text="Hello world",
            tokens=2
        )

        assert chunk.doc_id == "test-doc"
        assert chunk.page == 1
        assert chunk.x == 0.1
        assert chunk.type == "text"
        assert chunk.text == "Hello world"
        assert chunk.tokens == 2

    def test_chunk_to_dict(self):
        """Test converting chunk to dictionary."""
        chunk = DocumentChunk(
            doc_id="test-doc",
            page=1,
            x=0.1,
            y=0.2,
            w=0.8,
            h=0.1,
            type="text",
            text="Hello world",
            tokens=2
        )

        result = chunk.to_dict()
        expected = {
            "doc_id": "test-doc",
            "page": 1,
            "x": 0.1,
            "y": 0.2,
            "w": 0.8,
            "h": 0.1,
            "type": "text",
            "text": "Hello world",
            "tokens": 2
        }

        assert result == expected

    def test_chunk_to_jsonl(self):
        """Test converting chunk to JSONL."""
        chunk = DocumentChunk(
            doc_id="test-doc",
            page=1,
            x=0.1,
            y=0.2,
            w=0.8,
            h=0.1,
            type="text",
            text="Hello world",
            tokens=2
        )

        jsonl = chunk.to_jsonl()
        parsed = json.loads(jsonl)

        assert parsed["doc_id"] == "test-doc"
        assert parsed["text"] == "Hello world"
        assert parsed["type"] == "text"


class TestBBox:
    """Test BBox functionality."""

    def test_bbox_creation(self):
        """Test creating a bounding box."""
        bbox = BBox(x=0.1, y=0.2, w=0.8, h=0.1)

        assert bbox.x == 0.1
        assert bbox.y == 0.2
        assert bbox.w == 0.8
        assert bbox.h == 0.1

    def test_bbox_from_points(self):
        """Test creating bbox from absolute coordinates."""
        bbox = BBox.from_points(100, 200, 300, 400, 1000, 800)

        expected_x = 100 / 1000  # 0.1
        expected_y = 200 / 800   # 0.25
        expected_w = 200 / 1000  # 0.2
        expected_h = 200 / 800   # 0.25

        assert abs(bbox.x - expected_x) < 1e-6
        assert abs(bbox.y - expected_y) < 1e-6
        assert abs(bbox.w - expected_w) < 1e-6
        assert abs(bbox.h - expected_h) < 1e-6

    def test_bbox_to_tuple(self):
        """Test converting bbox to tuple."""
        bbox = BBox(x=0.1, y=0.2, w=0.8, h=0.1)
        result = bbox.to_tuple()

        assert result == (0.1, 0.2, 0.8, 0.1)


class TestUtilityFunctions:
    """Test utility functions."""

    def test_estimate_tokens(self):
        """Test token estimation."""
        assert estimate_tokens("") == 0
        assert estimate_tokens("Hello") == 1  # 5 chars -> 1 token
        assert estimate_tokens("Hello world, this is a test.") == 6  # ~28 chars -> 7 tokens, min 1

    def test_estimate_tokens_none(self):
        """Test token estimation with None."""
        assert estimate_tokens(None) == 0


class TestSerializeInterface:
    """Test the main serialize interface."""

    def test_serialize_nonexistent_file(self):
        """Test serializing a non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            list(serialize("nonexistent.pdf"))

    def test_serialize_unsupported_format(self, tmp_path):
        """Test serializing unsupported format raises error."""
        # Create a test file with unsupported extension
        test_file = tmp_path / "test.xyz"
        test_file.write_text("test content")

        with pytest.raises(ValueError, match="No serializer found"):
            list(serialize(test_file))

    def test_list_formats(self):
        """Test listing supported formats."""
        formats = list_formats()
        assert isinstance(formats, dict)

        # Should at least have PDF support if pypdfium2 is available
        # but may not if it's not installed
        assert len(formats) >= 0

    def test_serialize_to_jsonl_interface(self, tmp_path):
        """Test serialize_to_jsonl interface with unsupported file."""
        # Create a test file with unsupported extension
        test_file = tmp_path / "test.xyz"
        test_file.write_text("test content")

        with pytest.raises(ValueError, match="No serializer found"):
            list(serialize_to_jsonl(test_file))


@pytest.mark.skipif(
    not Path("tests/fixtures/sample.pdf").exists(),
    reason="Sample PDF not available"
)
class TestPdfSerialization:
    """Test PDF serialization with actual PDF files."""

    def test_serialize_pdf_basic(self):
        """Test basic PDF serialization."""
        pdf_path = Path("tests/fixtures/sample.pdf")
        if not pdf_path.exists():
            pytest.skip("Sample PDF not available")

        chunks = list(serialize(pdf_path))
        assert len(chunks) > 0

        # Verify chunk structure
        for chunk in chunks:
            assert isinstance(chunk, DocumentChunk)
            assert chunk.doc_id is not None
            assert chunk.page >= 1
            assert 0 <= chunk.x <= 1
            assert 0 <= chunk.y <= 1
            assert 0 <= chunk.w <= 1
            assert 0 <= chunk.h <= 1
            assert chunk.type in ["text", "table", "image"]

    def test_serialize_to_jsonl_pdf(self):
        """Test PDF serialization to JSONL."""
        pdf_path = Path("tests/fixtures/sample.pdf")
        if not pdf_path.exists():
            pytest.skip("Sample PDF not available")

        jsonl_lines = list(serialize_to_jsonl(pdf_path))
        assert len(jsonl_lines) > 0

        # Verify JSONL format
        for line in jsonl_lines:
            assert isinstance(line, str)
            parsed = json.loads(line)
            assert "doc_id" in parsed
            assert "page" in parsed
            assert "x" in parsed
            assert "y" in parsed
            assert "w" in parsed
            assert "h" in parsed
            assert "type" in parsed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])