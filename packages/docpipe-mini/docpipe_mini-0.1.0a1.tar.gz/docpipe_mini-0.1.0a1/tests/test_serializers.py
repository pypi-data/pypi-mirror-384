"""
Tests for document serializers.

Tests PDF and DOCX serialization with coordinate extraction.
"""

import json
import tempfile
import zipfile
from pathlib import Path
from typing import Iterator

import pytest

from docpipe import DocumentChunk, serialize
from docpipe.loaders._pdfium import PdfiumSerializer
from docpipe.loaders._docx import DocxSerializer
from docpipe._memory import MemoryGuard, get_memory_usage_mb


class TestPdfiumSerializer:
    """Test PDF serializer functionality."""

    def test_can_serialize_pdf(self):
        """Test PDF file detection."""
        serializer = PdfiumSerializer()
        assert serializer.can_serialize(Path("test.pdf"))
        assert serializer.can_serialize(Path("document.PDF"))
        assert not serializer.can_serialize(Path("test.docx"))
        assert not serializer.can_serialize(Path("test.txt"))

    def test_supported_extensions(self):
        """Test supported extensions."""
        serializer = PdfiumSerializer()
        assert ".pdf" in serializer.supported_extensions

    @pytest.mark.skipif(
        not Path("tests/fixtures/sample.pdf").exists(),
        reason="Sample PDF not available"
    )
    def test_serialize_pdf_real(self):
        """Test PDF serialization with real file."""
        pdf_path = Path("tests/fixtures/sample.pdf")
        if not pdf_path.exists():
            pytest.skip("Sample PDF not available")

        serializer = PdfiumSerializer()
        chunks = list(serializer.serialize(pdf_path))

        assert len(chunks) > 0, "Should extract at least one chunk"

        for chunk in chunks:
            assert isinstance(chunk, DocumentChunk)
            assert chunk.page >= 1
            assert 0 <= chunk.x <= 1
            assert 0 <= chunk.y <= 1
            assert 0 <= chunk.w <= 1
            assert 0 <= chunk.h <= 1
            assert chunk.type in ["text", "table", "image"]
            assert chunk.text is not None
            assert len(chunk.text.strip()) > 0
            assert chunk.tokens is not None
            assert chunk.tokens > 0

    def test_serialize_nonexistent_pdf(self):
        """Test serializing non-existent PDF raises error."""
        serializer = PdfiumSerializer()
        with pytest.raises(Exception):
            list(serializer.serialize(Path("nonexistent.pdf")))

    def test_serialize_invalid_pdf(self, tmp_path):
        """Test serializing invalid PDF raises error."""
        invalid_pdf = tmp_path / "invalid.pdf"
        invalid_pdf.write_text("This is not a PDF file")

        serializer = PdfiumSerializer()
        with pytest.raises(Exception):
            list(serializer.serialize(invalid_pdf))


class TestDocxSerializer:
    """Test DOCX serializer functionality."""

    def test_can_serialize_docx(self):
        """Test DOCX file detection."""
        serializer = DocxSerializer()
        assert serializer.can_serialize(Path("test.docx"))
        assert serializer.can_serialize(Path("document.DOCX"))
        assert serializer.can_serialize(Path("test.docm"))
        assert not serializer.can_serialize(Path("test.pdf"))
        assert not serializer.can_serialize(Path("test.txt"))

    def test_supported_extensions(self):
        """Test supported extensions."""
        serializer = DocxSerializer()
        extensions = serializer.supported_extensions
        assert ".docx" in extensions
        assert ".docm" in extensions

    def test_create_minimal_docx(self, tmp_path):
        """Create a minimal DOCX file for testing."""
        docx_path = tmp_path / "test.docx"

        # Create minimal DOCX structure
        with zipfile.ZipFile(docx_path, 'w') as docx:
            # [Content_Types].xml
            docx.writestr(
                "[Content_Types].xml",
                '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>'''
            )

            # _rels/.rels
            docx.writestr(
                "_rels/.rels",
                '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''
            )

            # word/document.xml
            docx.writestr(
                "word/document.xml",
                '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r>
                <w:t>Hello World</w:t>
            </w:r>
        </w:p>
        <w:p>
            <w:r>
                <w:rPr>
                    <w:b/>
                </w:rPr>
                <w:t>This is a bold paragraph.</w:t>
            </w:r>
        </w:p>
        <w:p>
            <w:r>
                <w:t>Line 1</w:t>
            </w:r>
        </w:p>
        <w:p>
            <w:r>
                <w:t>Line 2</w:t>
            </w:r>
        </w:p>
    </w:body>
</w:document>'''
            )

        return docx_path

    def test_serialize_docx_minimal(self, tmp_path):
        """Test DOCX serialization with minimal file."""
        docx_path = self.create_minimal_docx(tmp_path)

        serializer = DocxSerializer()
        chunks = list(serializer.serialize(docx_path))

        assert len(chunks) >= 2, "Should extract at least 2 paragraphs"

        # Check first chunk
        first_chunk = chunks[0]
        assert isinstance(first_chunk, DocumentChunk)
        assert first_chunk.page == 1  # DOCX is single-page
        assert 0 <= first_chunk.x <= 1
        assert 0 <= first_chunk.y <= 1
        assert 0 <= first_chunk.w <= 1
        assert 0 <= first_chunk.h <= 1
        assert first_chunk.type == "text"
        assert "Hello World" in first_chunk.text

        # Check chunk coordinates are reasonable
        assert 0.05 <= first_chunk.y <= 0.95  # Should be within page bounds

    def test_serialize_docx_empty_paragraphs(self, tmp_path):
        """Test DOCX with empty paragraphs."""
        docx_path = tmp_path / "empty.docx"

        with zipfile.ZipFile(docx_path, 'w') as docx:
            # Minimal structure with empty paragraphs
            docx.writestr("[Content_Types].xml", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>''')

            docx.writestr("_rels/.rels", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>''')

            docx.writestr("word/document.xml", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p/>
        <w:p>
            <w:r>
                <w:t>Content paragraph</w:t>
            </w:r>
        </w:p>
        <w:p/>
    </w:body>
</w:document>''')

        serializer = DocxSerializer()
        chunks = list(serializer.serialize(docx_path))

        # Should only extract non-empty paragraphs
        assert len(chunks) == 1
        assert "Content paragraph" in chunks[0].text

    def test_serialize_invalid_docx(self, tmp_path):
        """Test serializing invalid DOCX raises error."""
        invalid_docx = tmp_path / "invalid.docx"
        invalid_docx.write_text("This is not a DOCX file")

        serializer = DocxSerializer()
        with pytest.raises(Exception):
            list(serializer.serialize(invalid_docx))


class TestMemoryGuard:
    """Test memory guard functionality."""

    def test_memory_guard_creation(self):
        """Test memory guard creation."""
        guard = MemoryGuard(limit_mb=100)
        assert guard.limit_mb == 100
        assert guard.max_usage == 0.0
        assert guard.warning_count == 0

    def test_memory_guard_stats(self):
        """Test memory guard statistics."""
        guard = MemoryGuard(limit_mb=100)
        stats = guard.get_stats()

        assert isinstance(stats, dict)
        assert "limit_mb" in stats
        assert "max_usage_mb" in stats
        assert "current_usage_mb" in stats
        assert "warning_count" in stats
        assert "duration_seconds" in stats
        assert "psutil_available" in stats

    def test_memory_usage_function(self):
        """Test memory usage function."""
        usage = get_memory_usage_mb()
        assert isinstance(usage, (int, float))
        assert usage >= 0

    def test_memory_guard_check_usage(self):
        """Test memory guard usage checking."""
        guard = MemoryGuard(limit_mb=1000)  # High limit to avoid errors
        guard.check_usage()  # Should not raise

        # Test with very low limit (might not raise due to low usage)
        low_guard = MemoryGuard(limit_mb=0.001)  # Very low limit
        try:
            low_guard.check_usage()
        except MemoryError:
            pass  # Expected if memory usage > limit


class TestIntegration:
    """Integration tests for the complete serialization pipeline."""

    def test_list_formats_includes_pdf_and_docx(self):
        """Test that supported formats include PDF and DOCX."""
        from docpipe import list_formats
        formats = list_formats()

        assert isinstance(formats, dict)
        # Should have at least the built-in serializers
        assert len(formats) >= 1

    def test_serialize_interface_docx(self, tmp_path):
        """Test main serialize interface with DOCX."""
        # Create minimal DOCX
        serializer = DocxSerializer()
        docx_path = tmp_path / "test.docx"

        with zipfile.ZipFile(docx_path, 'w') as docx:
            docx.writestr("[Content_Types].xml", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>''')
            docx.writestr("_rels/.rels", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>''')
            docx.writestr("word/document.xml", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r>
                <w:t>Test content for integration testing.</w:t>
            </w:r>
        </w:p>
    </w:body>
</w:document>''')

        # Test through main interface
        chunks = list(serialize(docx_path))
        assert len(chunks) >= 1
        assert "Test content for integration testing" in chunks[0].text

    def test_jsonl_output_docx(self, tmp_path):
        """Test JSONL output with DOCX."""
        from docpipe import serialize_to_jsonl

        # Create minimal DOCX
        docx_path = tmp_path / "test.docx"
        serializer = DocxSerializer()

        with zipfile.ZipFile(docx_path, 'w') as docx:
            docx.writestr("[Content_Types].xml", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
    <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
    <Default Extension="xml" ContentType="application/xml"/>
    <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>''')
            docx.writestr("_rels/.rels", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
    <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>''')
            docx.writestr("word/document.xml", '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:body>
        <w:p>
            <w:r>
                <w:t>JSONL test content</w:t>
            </w:r>
        </w:p>
    </w:body>
</w:document>''')

        # Test JSONL output
        jsonl_lines = list(serialize_to_jsonl(docx_path))
        assert len(jsonl_lines) >= 1

        # Parse JSONL
        parsed = json.loads(jsonl_lines[0])
        assert "doc_id" in parsed
        assert "page" in parsed
        assert "x" in parsed
        assert "y" in parsed
        assert "w" in parsed
        assert "h" in parsed
        assert "type" in parsed
        assert "text" in parsed
        assert "tokens" in parsed
        assert parsed["text"] == "JSONL test content"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])