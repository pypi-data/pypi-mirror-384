"""
PDF document loader implementation using PyMuPDF (fitz).

This module provides a PdfLoader class that extracts content from PDF documents
and produces typed streams for further processing in the pipeline.
"""

from __future__ import annotations

import logging
from typing import Iterable, Optional, Any, Union
from pathlib import Path

from ._init import LoaderMixin
from .._types import (
    PageStream, BlockStream, TableStream, ImageStream,
    TypedStream, ProcessingMetadata
)

logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False
    logger.warning("PyMuPDF not available. Install with: pip install pymupdf")


class PdfLoader(LoaderMixin):
    """
    PDF document loader that extracts content as typed streams.

    This loader processes PDF files and extracts:
    - PageStream: Full page content with layout preserved
    - BlockStream: Text blocks (paragraphs, headings, etc.)
    - TableStream: Detected tabular data
    - ImageStream: Extracted images

    Uses PyMuPDF for robust PDF parsing with high-quality text extraction.
    """

    def __init__(self, *, max_mem_mb: Optional[int] = None, extract_images: bool = True):
        """
        Initialize the PDF loader.

        Args:
            max_mem_mb: Memory limit for processing large PDFs
            extract_images: Whether to extract images from PDFs
        """
        super().__init__(max_mem_mb=max_mem_mb)
        self.extract_images = extract_images

        if not FITZ_AVAILABLE:
            raise ImportError(
                "PyMuPDF is required for PDF loading. "
                "Install with: pip install pymupdf"
            )

    def can_load(self, source: Union[str, TypedStream]) -> bool:
        """
        Check if the source is a PDF file.

        Args:
            source: The document source

        Returns:
            True if source is a PDF file, False otherwise
        """
        if isinstance(source, str):
            return Path(source).suffix.lower() == '.pdf'
        elif hasattr(source, 'name'):
            return str(source.name).lower().endswith('.pdf')
        else:
            return False

    def load(
        self,
        source: Union[str, TypedStream],
        *,
        max_mem_mb: Optional[int] = None,
        **metadata: Any
    ) -> Iterable[TypedStream]:
        """
        Load PDF and extract content as typed streams.

        Args:
            source: PDF file path or stream
            max_mem_mb: Memory limit override
            **metadata: Additional processing metadata

        Yields:
            TypedStream objects containing PDF content
        """
        self._validate_source(source)
        self._check_memory_limit(source, max_mem_mb)

        logger.info(f"Loading PDF: {source}")

        try:
            # Open PDF document
            doc = self._open_pdf(source)

            # Add PDF metadata
            pdf_metadata = self._extract_pdf_metadata(doc, **metadata)

            # Process each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                logger.debug(f"Processing page {page_num + 1}")

                # Extract different content types
                yield from self._extract_page_content(page, page_num + 1, pdf_metadata)

            doc.close()
            logger.info(f"Completed PDF loading: {source}")

        except Exception as e:
            logger.error(f"Error loading PDF {source}: {e}")
            raise

    def _open_pdf(self, source: Union[str, TypedStream]) -> fitz.Document:
        """
        Open PDF document using PyMuPDF.

        Args:
            source: PDF source

        Returns:
            PyMuPDF document object
        """
        if isinstance(source, str):
            return fitz.open(source)
        else:
            # For streams, we need to save to temporary file or read bytes
            source.seek(0)
            pdf_bytes = source.read()
            return fitz.open(stream=pdf_bytes)

    def _extract_pdf_metadata(self, doc: fitz.Document, **extra: Any) -> ProcessingMetadata:
        """
        Extract metadata from PDF document.

        Args:
            doc: PyMuPDF document
            **extra: Additional metadata fields

        Returns:
            Processing metadata dictionary
        """
        metadata = {
            "pdf_title": doc.metadata.get('title', ''),
            "pdf_author": doc.metadata.get('author', ''),
            "pdf_subject": doc.metadata.get('subject', ''),
            "pdf_creator": doc.metadata.get('creator', ''),
            "pdf_producer": doc.metadata.get('producer', ''),
            "pdf_creation_date": doc.metadata.get('creationDate', ''),
            "pdf_modification_date": doc.metadata.get('modDate', ''),
            "page_count": len(doc),
            "is_encrypted": doc.is_encrypted,
            "pdf_version": doc.pdf_version(),
        }

        metadata.update(extra)
        return metadata

    def _extract_page_content(
        self,
        page: fitz.Page,
        page_number: int,
        doc_metadata: ProcessingMetadata
    ) -> Iterable[TypedStream]:
        """
        Extract content from a PDF page.

        Args:
            page: PyMuPDF page object
            page_number: Page number (1-based)
            doc_metadata: Document metadata

        Yields:
            TypedStream objects with page content
        """
        # Page dimensions and metadata
        page_metadata = {
            **doc_metadata,
            "page_number": page_number,
            "page_width": page.rect.width,
            "page_height": page.rect.height,
            "page_rotation": page.rotation,
        }

        # 1. Extract full page content
        page_text = page.get_text()
        if page_text.strip():
            yield PageStream(page_text, page_number, **page_metadata)

        # 2. Extract text blocks
        blocks = page.get_text("dict")["blocks"]
        for i, block in enumerate(blocks):
            if "lines" in block:  # Text block
                block_text = self._extract_block_text(block)
                if block_text.strip():
                    block_metadata = {
                        **page_metadata,
                        "block_number": i + 1,
                        "block_type": self._detect_block_type(block_text),
                        "bbox": block["bbox"],
                    }
                    yield BlockStream(
                        block_text,
                        block_type=block_metadata["block_type"],
                        **block_metadata
                    )

            elif "lines" not in block and "image" in block:
                # Image block
                if self.extract_images:
                    yield from self._extract_image_from_block(
                        block, page_number, i + 1, page_metadata
                    )

        # 3. Detect and extract tables (simplified implementation)
        yield from self._extract_tables_from_page(page, page_number, page_metadata)

    def _extract_block_text(self, block: dict) -> str:
        """
        Extract text from a text block.

        Args:
            block: Text block dictionary from PyMuPDF

        Returns:
            Concatenated text from all lines in the block
        """
        lines = []
        for line in block["lines"]:
            line_text = ""
            for span in line["spans"]:
                line_text += span["text"]
            lines.append(line_text.strip())
        return "\n".join(filter(None, lines))

    def _detect_block_type(self, text: str) -> str:
        """
        Detect the type of text block based on content.

        Args:
            text: Block text content

        Returns:
            Block type identifier
        """
        text = text.strip()

        # Heading detection
        if len(text) < 100 and text.isupper():
            return "heading"
        elif text.endswith(':') and len(text) < 100:
            return "heading"

        # List detection
        if text.startswith(('•', '-', '*', '1.', '2.', '3.')):
            return "list_item"

        # Table detection (simplified)
        if '\t' in text or '|' in text:
            return "table_candidate"

        # Default to paragraph
        return "paragraph"

    def _extract_image_from_block(
        self,
        block: dict,
        page_number: int,
        block_number: int,
        page_metadata: ProcessingMetadata
    ) -> Iterable[ImageStream]:
        """
        Extract image from PDF block.

        Args:
            block: Image block from PyMuPDF
            page_number: Page number
            block_number: Block number
            page_metadata: Page metadata

        Yields:
            ImageStream with extracted image data
        """
        try:
            # Get image data
            xref = block["image"]
            base_image = block["parent"].parent.extract_image(xref)
            image_bytes = base_image["image"]

            image_metadata = {
                **page_metadata,
                "block_number": block_number,
                "image_format": base_image["ext"],
                "image_width": base_image["width"],
                "image_height": base_image["height"],
                "image_colorspace": base_image["colorspace"],
                "bbox": block["bbox"],
            }

            yield ImageStream(
                image_bytes,
                format=base_image["ext"],
                **image_metadata
            )

        except Exception as e:
            logger.warning(f"Failed to extract image from block {block_number}: {e}")

    def _extract_tables_from_page(
        self,
        page: fitz.Page,
        page_number: int,
        page_metadata: ProcessingMetadata
    ) -> Iterable[TableStream]:
        """
        Extract tables from PDF page (simplified implementation).

        Args:
            page: PyMuPDF page object
            page_number: Page number
            page_metadata: Page metadata

        Yields:
            TableStream with detected table data
        """
        try:
            # Use PyMuPDF's table detection (available in recent versions)
            tables = page.find_tables()

            for i, table in enumerate(tables):
                table_data = table.extract()

                # Convert table data to CSV-like string
                table_text = self._table_to_text(table_data)

                table_metadata = {
                    **page_metadata,
                    "table_number": i + 1,
                    "table_rows": len(table_data),
                    "table_cols": len(table_data[0]) if table_data else 0,
                    "table_bbox": table.bbox,
                }

                yield TableStream(
                    table_text,
                    rows=table_metadata["table_rows"],
                    cols=table_metadata["table_cols"],
                    **table_metadata
                )

        except Exception as e:
            # Table detection not available or failed
            logger.debug(f"Table detection not available or failed: {e}")

    def _table_to_text(self, table_data: list[list[str]]) -> str:
        """
        Convert table data to text format.

        Args:
            table_data: 2D array of table cell contents

        Returns:
            Table content as delimited text
        """
        if not table_data:
            return ""

        # Use tab as delimiter for simplicity
        rows = []
        for row in table_data:
            # Clean cell content and join with tabs
            clean_row = [str(cell).strip() for cell in row]
            rows.append("\t".join(clean_row))

        return "\n".join(rows)

    @property
    def supported_formats(self) -> list[str]:
        """List of supported file formats."""
        return [".pdf"]