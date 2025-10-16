"""
Zero-dependency PDF serializer using pypdfium2.

BSD license fallback for PDF processing when PyMuPDF is not available.
Focus: coordinate extraction + text serialization for AI consumption.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterator, Optional, Dict, Any

try:
    import pypdfium2  # BSD license
    PYPDFIUM2_AVAILABLE = True
except ImportError:
    PYPDFIUM2_AVAILABLE = False

from .._types import DocumentChunk, BBox, ContentType, estimate_tokens
from .._protocols import DocumentSerializer

logger = logging.getLogger(__name__)


class PdfiumSerializer(DocumentSerializer):
    """
    PDF serializer using pypdfium2 (BSD license).

    Extracts text with coordinates using pypdfium2's native text extraction.
    Provides good performance for most PDFs without AGPL dependencies.
    """

    def __init__(self, *, min_chunk_length: int = 10):
        """
        Initialize the PDF serializer.

        Args:
            min_chunk_length: Minimum text length for a chunk
        """
        if not PYPDFIUM2_AVAILABLE:
            raise ImportError(
                "pypdfium2 is required for PDF processing. "
                "Install with: pip install pypdfium2"
            )
        self.min_chunk_length = min_chunk_length

    def can_serialize(self, file_path: Path) -> bool:
        """Check if file is a PDF."""
        return file_path.suffix.lower() == '.pdf'

    def serialize(
        self,
        file_path: Path,
        *,
        max_mem_mb: Optional[int] = None
    ) -> Iterator[DocumentChunk]:
        """
        Serialize PDF document into coordinate-aware chunks.

        Args:
            file_path: Path to PDF file
            max_mem_mb: Memory limit (not implemented for pypdfium2)

        Yields:
            DocumentChunk objects with text and coordinates
        """
        logger.info(f"Processing PDF with pypdfium2: {file_path}")

        try:
            # Open PDF with pypdfium2
            pdf = pypdfium2.PdfDocument(file_path)

            # Process each page
            for page_num in range(len(pdf)):
                page = pdf[page_num]
                logger.debug(f"Processing page {page_num + 1}")

                # Get page dimensions for coordinate normalization
                page_width = page.get_width()
                page_height = page.get_height()

                # Extract text with coordinates
                text_page = page.get_textpage()
                text_chunks = self._extract_text_chunks(
                    text_page, page_num + 1, page_width, page_height
                )

                # Close text page
                text_page.close()

                # Extract images
                image_chunks = self._extract_images(
                    page, page_num + 1, page_width, page_height
                )

                # Yield all chunks (text + images)
                for chunk in text_chunks:
                    yield chunk

                for chunk in image_chunks:
                    yield chunk

                # Close page
                page.close()

            # Close document
            pdf.close()

            logger.info(f"Completed PDF processing: {file_path}")

        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {e}")
            raise

    def _extract_text_chunks(
        self,
        text_page,
        page_num: int,
        page_width: float,
        page_height: float
    ) -> list[DocumentChunk]:
        """
        Extract text chunks with improved coordinates from a PDF text page.

        Uses pypdfium2's text block extraction for better coordinate accuracy.

        Args:
            text_page: pypdfium2 text page object
            page_num: Page number (1-based)
            page_width: Page width in points
            page_height: Page height in points

        Returns:
            List of DocumentChunk objects
        """
        chunks = []

        try:
            # Try to get text blocks first (better coordinates)
            text_blocks = []
            try:
                # pypdfium2 4+ supports get_text_blocks
                text_blocks = text_page.get_text_blocks()
            except AttributeError:
                # Fallback to manual block detection
                text_blocks = self._extract_blocks_manually(text_page, page_width, page_height)

            # Process each text block
            for block_idx, block in enumerate(text_blocks):
                if isinstance(block, (list, tuple)) and len(block) >= 5:
                    # Format: (text, x1, y1, x2, y2, ...) - coordinates in points
                    text = str(block[0]) if block[0] else ""
                    if not text.strip():
                        continue

                    x1, y1, x2, y2 = float(block[1]), float(block[2]), float(block[3]), float(block[4])

                    # Normalize coordinates
                    norm_bbox = BBox.from_points(
                        x1, y1, x2, y2, page_width, page_height
                    )

                    # Detect content type
                    content_type = self._detect_content_type(text)

                    # Prepare metadata for tables
                    metadata = None
                    if content_type == ContentType.TABLE:
                        # Try to parse table structure
                        try:
                            table_data = self._parse_table_structure(text.strip())
                            metadata = {
                                "table_structure": table_data,
                                "extraction_method": "text_based"
                            }
                        except Exception as table_error:
                            logger.debug(f"Could not parse table structure: {table_error}")
                            metadata = {"parsing_error": str(table_error)}

                    # Create chunk
                    chunk = DocumentChunk(
                        doc_id="",  # Will be set by serialize()
                        page=page_num,
                        x=norm_bbox.x,
                        y=norm_bbox.y,
                        w=norm_bbox.w,
                        h=norm_bbox.h,
                        type=content_type,
                        text=text.strip(),
                        tokens=estimate_tokens(text.strip()),
                        metadata=metadata
                    )
                    chunks.append(chunk)

                elif isinstance(block, str):
                    # Simple text without coordinates - estimate position
                    if not block.strip():
                        continue

                    # Estimate position based on block order
                    estimated_bbox = BBox(
                        x=0.1,
                        y=0.1 + (block_idx * 0.05),  # Stack vertically
                        w=0.8,
                        h=min(0.05, len(block) / 1000)  # Height based on length
                    )

                    chunk = DocumentChunk(
                        doc_id="",  # Will be set by serialize()
                        page=page_num,
                        x=estimated_bbox.x,
                        y=estimated_bbox.y,
                        w=estimated_bbox.w,
                        h=estimated_bbox.h,
                        type=ContentType.TEXT,
                        text=block.strip(),
                        tokens=estimate_tokens(block.strip())
                    )
                    chunks.append(chunk)

        except Exception as e:
            logger.warning(f"Error in advanced coordinate extraction: {e}")

            # Ultimate fallback: full page text
            try:
                full_text = text_page.get_text_range()
                if full_text.strip():
                    # Split into reasonable chunks
                    paragraphs = full_text.split('\n\n')
                    for i, para in enumerate(paragraphs):
                        if not para.strip():
                            continue

                        # Estimate position
                        y_pos = 0.1 + (i / len(paragraphs)) * 0.8
                        estimated_bbox = BBox(
                            x=0.1, y=y_pos, w=0.8,
                            h=min(0.1, len(para) / 500)
                        )

                        chunk = DocumentChunk(
                            doc_id="",  # Will be set by serialize()
                            page=page_num,
                            x=estimated_bbox.x,
                            y=estimated_bbox.y,
                            w=estimated_bbox.w,
                            h=estimated_bbox.h,
                            type=ContentType.TEXT,
                            text=para.strip(),
                            tokens=estimate_tokens(para.strip())
                        )
                        chunks.append(chunk)

            except Exception as fallback_error:
                logger.error(f"Failed to extract page text: {fallback_error}")

        return chunks

    def _extract_blocks_manually(self, text_page, page_width: float, page_height: float) -> list:
        """
        Manually extract text blocks when get_text_blocks is not available.

        Args:
            text_page: pypdfium2 text page object
            page_width: Page width in points
            page_height: Page height in points

        Returns:
            List of text blocks with estimated coordinates
        """
        blocks = []
        try:
            # Get full text and split into paragraphs
            full_text = text_page.get_text_range()
            paragraphs = [p.strip() for p in full_text.split('\n\n') if p.strip()]

            # Estimate coordinates for each paragraph
            for i, paragraph in enumerate(paragraphs):
                # Simple vertical stacking estimation
                y_pos = 0.1 + (i / len(paragraphs)) * 0.8 if paragraphs else 0.5
                height = min(0.1, len(paragraph) / 1000)

                blocks.append((
                    paragraph,
                    72,  # x1 in points (1 inch)
                    y_pos * page_height,  # y1 in points
                    page_width - 72,  # x2 in points
                    (y_pos + height) * page_height  # y2 in points
                ))

        except Exception as e:
            logger.debug(f"Manual block extraction failed: {e}")

        return blocks

    def _detect_content_type(self, text: str) -> str:
        """
        Detect content type based on text patterns.

        Args:
            text: Text content

        Returns:
            Content type identifier
        """
        text = text.strip()

        # Heading detection
        if len(text) < 100 and (
            text.isupper() or
            text.endswith(':') or
            any(text.startswith(prefix) for prefix in ['Chapter', 'Section', 'Part', 'Abstract'])
        ):
            return ContentType.TEXT

        # Table detection
        lines = text.split('\n')
        if len(lines) > 2:
            # Check for consistent column patterns
            has_tabs = any('\t' in line for line in lines[:5])
            has_pipes = any('|' in line for line in lines[:5])
            if (has_tabs or has_pipes) and all(len(line.strip()) > 0 for line in lines[:3]):
                return ContentType.TABLE

        # List detection
        if any(text.startswith(prefix) for prefix in ['•', '-', '*', '1.', '2.', '3.']):
            return ContentType.TEXT

        return ContentType.TEXT

    def _extract_images(
        self,
        page,
        page_num: int,
        page_width: float,
        page_height: float
    ) -> list[DocumentChunk]:
        """
        Extract images from a PDF page.

        Args:
            page: pypdfium2 page object
            page_num: Page number (1-based)
            page_width: Page width in points
            page_height: Page height in points

        Returns:
            List of DocumentChunk objects representing images
        """
        image_chunks = []

        try:
            # Get page objects and look for images
            page_objects = page.get_objects()

            # Use a set to track unique image positions and avoid duplicates
            seen_positions = set()

            for obj in page_objects:
                try:
                    # Check if this is an image object
                    if hasattr(obj, 'type'):
                        obj_type = obj.type
                        # PDF object types: 1=text, 2=image, 3=path, 4=shading, 5=form
                        if obj_type == 2:  # Image object
                            # Try to get image bounds
                            if hasattr(obj, 'get_pos'):
                                try:
                                    x, y, w, h = obj.get_pos()
                                    if w > 0 and h > 0:
                                        # Filter out very small images (likely icons or decorative elements)
                                        # Only include images larger than 1% of page area
                                        page_area = page_width * page_height
                                        image_area = w * h
                                        relative_size = image_area / page_area

                                        if relative_size > 0.01:  # At least 1% of page area
                                            # Round coordinates to avoid near-duplicates
                                            pos_key = (round(x, 1), round(y, 1), round(w, 1), round(h, 1))

                                            if pos_key not in seen_positions:
                                                seen_positions.add(pos_key)

                                                # Normalize coordinates
                                                norm_bbox = BBox(
                                                    x=x / page_width,
                                                    y=y / page_height,
                                                    w=w / page_width,
                                                    h=h / page_height
                                                )

                                                # Try to extract actual image data
                                                binary_data = None
                                                metadata = {"source": "pypdfium2", "format": "unknown"}

                                                try:
                                                    # Try to get bitmap data from the image object
                                                    if hasattr(obj, 'get_bitmap'):
                                                        bitmap = obj.get_bitmap()
                                                        if bitmap:
                                                            # Convert bitmap to bytes
                                                            binary_data = bitmap.to_bytes()

                                                            # Try to determine image format
                                                            if hasattr(bitmap, 'get_width') and hasattr(bitmap, 'get_height'):
                                                                metadata.update({
                                                                    "width": bitmap.get_width(),
                                                                    "height": bitmap.get_height(),
                                                                    "format": "bitmap"
                                                                })

                                                            metadata["extraction_method"] = "bitmap"

                                                except Exception as bitmap_error:
                                                    logger.debug(f"Could not extract bitmap: {bitmap_error}")
                                                    metadata["extraction_error"] = str(bitmap_error)

                                                # Create image chunk with binary data
                                                chunk = DocumentChunk(
                                                    doc_id="",  # Will be set by serialize()
                                                    page=page_num,
                                                    x=norm_bbox.x,
                                                    y=norm_bbox.y,
                                                    w=norm_bbox.w,
                                                    h=norm_bbox.h,
                                                    type=ContentType.IMAGE,
                                                    text=None,  # Pure image has no text
                                                    tokens=None,
                                                    binary_data=binary_data,
                                                    metadata=metadata
                                                )
                                                image_chunks.append(chunk)
                                except Exception as pos_error:
                                    logger.debug(f"Could not get image position: {pos_error}")

                except Exception as obj_error:
                    logger.debug(f"Error processing page object: {obj_error}")
                    continue

        except Exception as e:
            logger.debug(f"Error extracting images from page {page_num}: {e}")

        return image_chunks

    def _parse_table_structure(self, text: str) -> Dict[str, Any]:
        """
        Parse table structure from text content.

        Args:
            text: Table text content

        Returns:
            Dictionary with table structure information
        """
        lines = text.strip().split('\n')
        rows = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try different delimiters
            if '|' in line:
                # Pipe-delimited table
                cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            elif '\t' in line:
                # Tab-delimited table
                cells = line.split('\t')
            else:
                # Space-delimited or simple table
                cells = [line]

            if cells:
                rows.append({
                    "cells": cells,
                    "cell_count": len(cells)
                })

        return {
            "rows": rows,
            "row_count": len(rows),
            "has_header": len(rows) > 1,
            "max_columns": max([r["cell_count"] for r in rows]) if rows else 0
        }

    @property
    def supported_extensions(self) -> list[str]:
        """Return supported file extensions."""
        return [".pdf"]