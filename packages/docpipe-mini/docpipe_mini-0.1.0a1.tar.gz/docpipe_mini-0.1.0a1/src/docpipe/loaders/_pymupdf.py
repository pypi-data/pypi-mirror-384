"""
PDF serializer using PyMuPDF (AGPL license).

High-performance PDF processing with accurate image and text extraction.
Better for documents with complex layouts and embedded images.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterator, Optional, Dict, Any

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

from .._types import DocumentChunk, BBox, ContentType, estimate_tokens
from .._protocols import DocumentSerializer

logger = logging.getLogger(__name__)


class PyMuPDFSerializer(DocumentSerializer):
    """
    PDF serializer using PyMuPDF (AGPL license).

    Provides accurate text extraction, image detection, and table recognition
    for complex PDF documents. Better handling of embedded graphics and layouts.
    """

    def __init__(self, *, min_chunk_length: int = 10):
        """
        Initialize the PyMuPDF serializer.

        Args:
            min_chunk_length: Minimum text length for a chunk
        """
        if not PYMUPDF_AVAILABLE:
            raise ImportError(
                "PyMuPDF is required for this PDF processor. "
                "Install with: pip install PyMuPDF"
            )
        self.min_chunk_length = min_chunk_length

    def can_serialize(self, file_path: Path) -> bool:
        """Check if file is a PDF."""
        return str(file_path).lower().endswith('.pdf')

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
            max_mem_mb: Memory limit (not implemented for PyMuPDF)

        Yields:
            DocumentChunk objects with text and coordinates
        """
        logger.info(f"Processing PDF with PyMuPDF: {file_path}")

        try:
            # Open PDF with PyMuPDF
            pdf = fitz.open(file_path)

            # Prepare document metadata
            document_metadata = {
                "source_file": str(file_path),
                "file_name": file_path.name,
                "file_extension": file_path.suffix,
                "file_size": file_path.stat().st_size if file_path.exists() else 0
            }

            # Process each page
            for page_num in range(len(pdf)):
                page = pdf[page_num]
                logger.debug(f"Processing page {page_num + 1}")

                # Get page dimensions for coordinate normalization
                page_rect = page.rect
                page_width = page_rect.width
                page_height = page_rect.height

                # Extract text with coordinates
                text_chunks = self._extract_text_chunks(
                    page, page_num + 1, page_width, page_height, document_metadata
                )

                # Extract images with better accuracy
                image_chunks = self._extract_images(
                    page, page_num + 1, page_width, page_height, document_metadata
                )

                # Extract tables
                table_chunks = self._extract_tables(
                    page, page_num + 1, page_width, page_height, document_metadata
                )

                # Yield all chunks
                for chunk in text_chunks:
                    yield chunk

                for chunk in image_chunks:
                    yield chunk

                for chunk in table_chunks:
                    yield chunk

            # Close document
            pdf.close()

            logger.info(f"Completed PDF processing: {file_path}")

        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {e}")
            raise

    def _extract_text_chunks(
        self,
        page,
        page_num: int,
        page_width: float,
        page_height: float,
        document_metadata: Dict[str, Any]
    ) -> list[DocumentChunk]:
        """
        Extract text chunks with coordinates from a PyMuPDF page.

        Uses PyMuPDF's text block detection for better accuracy.

        Args:
            page: PyMuPDF page object
            page_num: Page number (1-based)
            page_width: Page width in points
            page_height: Page height in points

        Returns:
            List of DocumentChunk objects
        """
        chunks = []

        try:
            # Get text blocks
            text_blocks = page.get_text("dict")

            if "blocks" in text_blocks:
                for block in text_blocks["blocks"]:
                    if block["type"] == 0:  # Text block
                        # Extract the entire block as one chunk (paragraph-level)
                        block_text = ""
                        block_bbox = None
                        font_info = {}

                        lines = block.get("lines", [])
                        for line in lines:
                            line_text = ""
                            for span in line.get("spans", []):
                                span_text = span.get("text", "")
                                if span_text:
                                    line_text += span_text

                                    # Track font information (use most common font)
                                    font_name = span.get("font", "")
                                    if font_name:
                                        font_info[font_name] = font_info.get(font_name, 0) + 1

                            if line_text:
                                block_text += line_text + " "

                        # Remove trailing space and strip
                        block_text = block_text.strip()

                        if len(block_text) >= self.min_chunk_length:
                            # Get block bounding box
                            block_bbox = block.get("bbox", [0, 0, 0, 0])
                            x1, y1, x2, y2 = block_bbox

                            # Normalize coordinates
                            norm_bbox = BBox.from_points(
                                x1, y1, x2, y2, page_width, page_height
                            )

                            # Get most common font for the block
                            primary_font = max(font_info.items(), key=lambda x: x[1])[0] if font_info else ""

                            # Create text chunk for the entire block
                            chunk = DocumentChunk(
                                doc_id="",
                                page=page_num,
                                x=norm_bbox.x,
                                y=norm_bbox.y,
                                w=norm_bbox.w,
                                h=norm_bbox.h,
                                type=ContentType.TEXT,
                                text=block_text,
                                tokens=estimate_tokens(block_text),
                                metadata={
                                    **document_metadata,
                                    "font": primary_font,
                                    "block_type": "paragraph",
                                    "char_count": len(block_text),
                                    "extraction_method": "pymupdf_block"
                                }
                            )
                            chunks.append(chunk)

        except Exception as e:
            logger.warning(f"Error in PyMuPDF text extraction: {e}")

        return chunks

    def _extract_images(
        self,
        page,
        page_num: int,
        page_width: float,
        page_height: float,
        document_metadata: Dict[str, Any]
    ) -> list[DocumentChunk]:
        """
        Extract images from a PyMuPDF page.

        Args:
            page: PyMuPDF page object
            page_num: Page number (1-based)
            page_width: Page width in points
            page_height: Page height in points

        Returns:
            List of DocumentChunk objects representing images
        """
        image_chunks = []

        try:
            # Get image list
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                try:
                    # Get image rectangle
                    xref = img[0]
                    pix = fitz.Pixmap(page.parent, xref)

                    # Get image bounding box - try to get the bbox for this specific image
                    try:
                        img_rect = page.get_image_bbox(img)
                        x1, y1, x2, y2 = img_rect.x0, img_rect.y0, img_rect.x1, img_rect.y1

                        # Normalize coordinates
                        norm_bbox = BBox.from_points(
                            x1, y1, x2, y2, page_width, page_height
                        )
                    except:
                        # If bbox detection fails, create a default one based on image dimensions
                        # Place image in top-left corner with reasonable size
                        img_w, img_h = pix.width, pix.height
                        scale_factor = min(0.2, min(page_width / img_w, page_height / img_h))
                        norm_w = (img_w * scale_factor) / page_width
                        norm_h = (img_h * scale_factor) / page_height

                        norm_bbox = BBox(0.1, 0.1, norm_w, norm_h)

                    # Get actual image data
                    binary_data = None
                    try:
                        # Extract image as bytes
                        img_data = page.parent.extract_image(xref)
                        binary_data = img_data["image"]
                    except Exception as extract_error:
                        logger.debug(f"Could not extract image data: {extract_error}")

                    # Create image chunk
                    chunk = DocumentChunk(
                        doc_id="",
                        page=page_num,
                        x=norm_bbox.x,
                        y=norm_bbox.y,
                        w=norm_bbox.w,
                        h=norm_bbox.h,
                        type=ContentType.IMAGE,
                        text=None,
                        tokens=None,
                        binary_data=binary_data,
                        metadata={
                            **document_metadata,
                            "width": pix.width,
                            "height": pix.height,
                            "colorspace": str(pix.colorspace),
                            "xref": xref,
                            "format": "png",
                            "extraction_method": "pymupdf"
                        }
                    )
                    image_chunks.append(chunk)

                    # Clean up pixmap
                    pix = None

                except Exception as img_error:
                    logger.debug(f"Error processing image {img_index}: {img_error}")
                    continue

        except Exception as e:
            logger.debug(f"Error extracting images from page {page_num}: {e}")

        return image_chunks

    def _extract_tables(
        self,
        page,
        page_num: int,
        page_width: float,
        page_height: float,
        document_metadata: Dict[str, Any]
    ) -> list[DocumentChunk]:
        """
        Extract tables from a PyMuPDF page.

        Args:
            page: PyMuPDF page object
            page_num: Page number (1-based)
            page_width: Page width in points
            page_height: Page height in points

        Returns:
            List of DocumentChunk objects representing tables
        """
        table_chunks = []

        try:
            # Find tables on the page
            tables = page.find_tables()

            for table_index, table in enumerate(tables):
                try:
                    # Get table bounding box
                    table_bbox = table.bbox
                    x1, y1, x2, y2 = table_bbox.x0, table_bbox.y0, table_bbox.x1, table_bbox.y1

                    # Normalize coordinates
                    norm_bbox = BBox.from_points(
                        x1, y1, x2, y2, page_width, page_height
                    )

                    # Extract table data
                    table_data = []
                    for row_idx in range(table.row_count):
                        row_data = []
                        for col_idx in range(table.col_count):
                            try:
                                cell = table.extract_cell(row_idx, col_idx)
                                row_data.append(cell or "")
                            except:
                                row_data.append("")
                        table_data.append(row_data)

                    # Create table structure
                    table_structure = {
                        "rows": [
                            {"cells": row, "cell_count": len(row)}
                            for row in table_data
                        ],
                        "row_count": len(table_data),
                        "col_count": table.col_count,
                        "has_header": len(table_data) > 1,
                        "bbox": [x1, y1, x2, y2]
                    }

                    # Create table chunk
                    chunk = DocumentChunk(
                        doc_id="",
                        page=page_num,
                        x=norm_bbox.x,
                        y=norm_bbox.y,
                        w=norm_bbox.w,
                        h=norm_bbox.h,
                        type=ContentType.TABLE,
                        text="\n".join(["\t".join(row) for row in table_data]),
                        tokens=estimate_tokens("\n".join(["\t".join(row) for row in table_data])),
                        metadata={
                            **document_metadata,
                            "table_structure": table_structure,
                            "extraction_method": "pymupdf",
                            "table_index": table_index
                        }
                    )
                    table_chunks.append(chunk)

                except Exception as table_error:
                    logger.debug(f"Error processing table {table_index}: {table_error}")
                    continue

        except Exception as e:
            logger.debug(f"Error extracting tables from page {page_num}: {e}")

        return table_chunks

    @property
    def supported_extensions(self) -> list[str]:
        """Return supported file extensions."""
        return [".pdf"]