"""
docpipe - Minimal document-to-jsonl serializer.

Goal: 5 MB install, 300 ms/MB, zero model, zero OCR.
Just give AI clean text with coordinates.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterator, Union

from ._types import DocumentChunk, generate_doc_id
from ._protocols import get_serializer, register_serializer

# Import built-in serializers to auto-register them
# Try PyMuPDF first (better accuracy)
try:
    from .loaders._pymupdf import PyMuPDFSerializer
    register_serializer(PyMuPDFSerializer())
except ImportError:
    pass  # PyMuPDF not available

# Fallback to pypdfium2 (BSD license, zero dependencies)
try:
    from .loaders._pdfium import PdfiumSerializer
    register_serializer(PdfiumSerializer())
except ImportError:
    pass  # pypdfium2 not available

# DOCX serializer (stdlib only, always available)
from .loaders._docx import DocxSerializer
register_serializer(DocxSerializer())

# Simple user-facing API
def serialize(
    file_path: Union[str, Path],
    *,
    max_mem_mb: int = 512,
    doc_id: str | None = None
) -> Iterator[DocumentChunk]:
    """
    Serialize document into coordinate-aware chunks.

    This is the main user interface - converts any supported document
    into JSONL-ready chunks with coordinates.

    Args:
        file_path: Path to the document file
        max_mem_mb: Memory limit in MB (default: 512)
        doc_id: Optional document ID (auto-generated if None)

    Yields:
        DocumentChunk objects with coordinates and text

    Example:
        >>> for chunk in docpipe.serialize("paper.pdf"):
        ...     print(chunk.to_jsonl())
        {"doc_id":"...","page":1,"x":0.1,"y":0.2,"w":0.8,"h":0.1,"type":"text","text":"...","tokens":42}
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    # Get appropriate serializer
    serializer = get_serializer(path)
    if serializer is None:
        raise ValueError(f"No serializer found for file: {path.suffix}")

    # Generate doc ID if not provided
    if doc_id is None:
        doc_id = generate_doc_id()

    # Override doc_id in all chunks
    for chunk in serializer.serialize(path, max_mem_mb=max_mem_mb):
        chunk.doc_id = doc_id
        yield chunk


def serialize_to_jsonl(
    file_path: Union[str, Path],
    *,
    max_mem_mb: int = 512,
    output_file: Union[str, Path] | None = None
) -> Iterator[str]:
    """
    Serialize document directly to JSONL lines.

    Args:
        file_path: Path to the document file
        max_mem_mb: Memory limit in MB (default: 512)
        output_file: Optional output file path

    Yields:
        JSONL strings

    Example:
        >>> for line in docpipe.serialize_to_jsonl("paper.pdf"):
        ...     print(line)
        {"doc_id":"...","page":1,"x":0.1,"y":0.2,"w":0.8,"h":0.1,"type":"text","text":"...","tokens":42}
    """
    for chunk in serialize(file_path, max_mem_mb=max_mem_mb):
        yield chunk.to_jsonl()


# List supported formats
def list_formats() -> dict[str, list[str]]:
    """List all supported document formats."""
    from ._protocols import list_supported_formats
    return list_supported_formats()


# Version info
__version__ = "0.1.0a1"
__all__ = [
    "serialize",
    "serialize_to_jsonl",
    "list_formats",
    "DocumentChunk",
    "register_serializer",
    "get_serializer"
]

# CLI entry point (fallback when typer not available)
def _cli_main() -> None:
    """Simple command line interface."""
    if len(sys.argv) < 2:
        print("Usage: python -m docpipe <document_file> [output_file]")
        print("       python -m docpipe --help (for full CLI with typer)")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    try:
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                for line in serialize_to_jsonl(input_file):
                    f.write(line + '\n')
            print(f"Serialized {input_file} to {output_file}")
        else:
            for line in serialize_to_jsonl(input_file):
                print(line)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


# Enhanced CLI with typer (if available)
def cli_main() -> None:
    """Enhanced CLI interface."""
    try:
        from .cli import main as cli_entry
        cli_entry()
    except ImportError:
        _cli_main()


if __name__ == "__main__":
    cli_main()