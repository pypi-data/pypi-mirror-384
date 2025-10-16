"""
DOCX serializer using Python standard library.

Zero-dependency Word document parser using zipfile and xml.etree.
Extracts text with basic coordinate estimation for AI consumption.
"""

from __future__ import annotations

import logging
import zipfile
import xml.etree.ElementTree as ET
import base64
from pathlib import Path
from typing import Iterator, Optional, Dict, Any
from dataclasses import dataclass

from .._types import DocumentChunk, BBox, ContentType, estimate_tokens
from .._protocols import DocumentSerializer

logger = logging.getLogger(__name__)


@dataclass
class TextRun:
    """Represents a text run with formatting information."""
    text: str
    font_size: Optional[float] = None
    is_bold: bool = False
    is_italic: bool = False


class DocxSerializer(DocumentSerializer):
    """
    DOCX serializer using Python standard library only.

    Parses DOCX files by extracting text from document.xml and estimating
    coordinates based on document structure and formatting.
    """

    def __init__(self, *, min_chunk_length: int = 10):
        """
        Initialize the DOCX serializer.

        Args:
            min_chunk_length: Minimum text length for a chunk
        """
        self.min_chunk_length = min_chunk_length

    def can_serialize(self, file_path: Path) -> bool:
        """Check if file is a DOCX."""
        return file_path.suffix.lower() in ['.docx', '.docm']

    def serialize(
        self,
        file_path: Path,
        *,
        max_mem_mb: Optional[int] = None
    ) -> Iterator[DocumentChunk]:
        """
        Serialize DOCX document into coordinate-aware chunks.

        Args:
            file_path: Path to DOCX file
            max_mem_mb: Memory limit (not implemented for stdlib version)

        Yields:
            DocumentChunk objects with text and estimated coordinates
        """
        logger.info(f"Processing DOCX with stdlib: {file_path}")

        try:
            with zipfile.ZipFile(file_path, 'r') as docx:
                # Extract document structure
                if 'word/document.xml' not in docx.namelist():
                    raise ValueError("Invalid DOCX file: no document.xml found")

                # Parse main document
                document_xml = docx.read('word/document.xml')
                root = ET.fromstring(document_xml)

                # Define namespace
                namespaces = {
                    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
                    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
                }

                # Prepare document metadata
                document_metadata = {
                    "source_file": str(file_path),
                    "file_name": file_path.name,
                    "file_extension": file_path.suffix,
                    "file_size": file_path.stat().st_size if file_path.exists() else 0
                }

                # Extract paragraphs
                paragraphs = root.findall('.//w:p', namespaces)
                logger.debug(f"Found {len(paragraphs)} paragraphs")

                # Collect all chunks (text and images) for proper ordering
                all_chunks = []
                chunk_num = 0

                # Process text chunks
                for para_idx, paragraph in enumerate(paragraphs):
                    text_runs = self._extract_text_runs(paragraph, namespaces)
                    if not text_runs:
                        continue

                    # Combine runs into chunk text
                    chunk_text = ''.join(run.text for run in text_runs)
                    if len(chunk_text.strip()) < self.min_chunk_length:
                        continue

                    # Estimate coordinates based on paragraph position
                    chunk_num += 1
                    estimated_bbox = self._estimate_coordinates(
                        para_idx, len(paragraphs), len(text_runs)
                    )

                    # Detect content type
                    content_type = self._detect_content_type(chunk_text)

                    # Create document chunk
                    chunk = DocumentChunk(
                        doc_id="",  # Will be set by serialize()
                        page=1,  # DOCX is single-page conceptually
                        x=estimated_bbox.x,
                        y=estimated_bbox.y,
                        w=estimated_bbox.w,
                        h=estimated_bbox.h,
                        type=content_type,
                        text=chunk_text.strip(),
                        tokens=estimate_tokens(chunk_text.strip()),
                        metadata={
                            **document_metadata,
                            "font_size": text_runs[0].font_size if text_runs else None,
                            "is_bold": any(run.is_bold for run in text_runs),
                            "is_italic": any(run.is_italic for run in text_runs),
                            "extraction_method": "docx_stdlib"
                        }
                    )

                    logger.debug(f"Created text chunk {chunk_num}: {len(chunk_text)} chars")
                    all_chunks.append(chunk)

                # Extract images
                image_chunks = self._extract_images(docx, document_metadata)
                for chunk in image_chunks:
                    chunk_num += 1
                    logger.debug(f"Created image chunk {chunk_num}")
                    all_chunks.append(chunk)

                # Sort all chunks by y-coordinate to maintain document order
                all_chunks.sort(key=lambda c: (c.y, c.x))

                # Yield chunks in proper order
                for chunk in all_chunks:
                    yield chunk

                logger.info(f"Completed DOCX processing: {file_path}")

        except Exception as e:
            logger.error(f"Error processing DOCX {file_path}: {e}")
            raise

    def _extract_text_runs(self, paragraph: ET.Element, namespaces: dict) -> list[TextRun]:
        """
        Extract text runs from a paragraph with formatting information.

        Args:
            paragraph: Paragraph XML element
            namespaces: XML namespaces

        Returns:
            List of TextRun objects
        """
        runs = []

        for run in paragraph.findall('.//w:r', namespaces):
            # Extract text
            text_elements = run.findall('.//w:t', namespaces)
            run_text = ''.join(elem.text or '' for elem in text_elements)

            if not run_text.strip():
                continue

            # Extract formatting
            run_props = run.find('.//w:rPr', namespaces)
            font_size = None
            is_bold = False
            is_italic = False

            if run_props is not None:
                # Font size
                sz_elem = run_props.find('.//w:sz', namespaces)
                if sz_elem is not None and sz_elem.get('val'):
                    try:
                        font_size = float(sz_elem.get('val')) / 2.0  # Convert half-points to points
                    except (ValueError, TypeError):
                        pass

                # Bold
                b_elem = run_props.find('.//w:b', namespaces)
                if b_elem is not None:
                    is_bold = True

                # Italic
                i_elem = run_props.find('.//w:i', namespaces)
                if i_elem is not None:
                    is_italic = True

            runs.append(TextRun(
                text=run_text,
                font_size=font_size,
                is_bold=is_bold,
                is_italic=is_italic
            ))

        return runs

    def _estimate_coordinates(
        self,
        paragraph_idx: int,
        total_paragraphs: int,
        text_runs_count: int
    ) -> BBox:
        """
        Estimate coordinates for a paragraph based on its position.

        Since DOCX doesn't store absolute coordinates without complex layout
        calculation, we estimate based on document structure.

        Args:
            paragraph_idx: Paragraph index in document
            total_paragraphs: Total number of paragraphs
            text_runs_count: Number of text runs in paragraph

        Returns:
            Estimated bounding box
        """
        # Estimate vertical position (y) based on paragraph order
        y_pos = (paragraph_idx / max(total_paragraphs, 1)) * 0.9 + 0.05  # 5% to 95%

        # Estimate height based on content length and runs
        if text_runs_count == 1:
            height = 0.02  # Single line
        elif text_runs_count <= 3:
            height = 0.04  # Short paragraph
        else:
            height = min(0.02 * text_runs_count, 0.15)  # Multi-line paragraph

        # Standard width and position for text content
        x_pos = 0.1  # 10% margin
        width = 0.8  # 80% of page width

        return BBox(x=x_pos, y=y_pos, w=width, h=height)

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
            any(text.startswith(prefix) for prefix in ['Chapter', 'Section', 'Part', 'Figure', 'Table'])
        ):
            return ContentType.TEXT  # Still text, but could be used for styling

        # List detection
        if any(text.startswith(prefix) for prefix in ['•', '-', '*', '1.', '2.', '3.']):
            return ContentType.TEXT

        # Table detection (simple)
        if '\t' in text or '|' in text:
            lines = text.split('\n')
            if len(lines) > 1 and all('|' in line or '\t' in line for line in lines[:3]):
                return ContentType.TABLE

        # Default to text
        return ContentType.TEXT

    def _extract_images(self, docx: zipfile.ZipFile, document_metadata: Dict[str, Any]) -> list[DocumentChunk]:
        """
        Extract images from DOCX file.

        Args:
            docx: Opened DOCX zipfile
            document_metadata: Document metadata to include

        Returns:
            List of DocumentChunk objects representing images
        """
        image_chunks = []

        try:
            # Check if there's a media folder with images (more robust approach)
            media_files = [f for f in docx.namelist() if f.startswith('word/media/')]
            logger.debug(f"Found media files: {media_files}")

            # Sort media files to maintain order
            media_files.sort()

            for media_path in media_files:
                try:
                    # Extract image data
                    image_data = docx.read(media_path)

                    # Skip empty files
                    if not image_data:
                        continue

                    # Determine image format from file extension
                    filename = media_path.split('/')[-1]
                    image_format = 'unknown'
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp')):
                        image_format = filename.split('.')[-1].lower()

                    # Create binary data (base64 encoded)
                    binary_data = base64.b64encode(image_data).decode('utf-8')

                    # Estimate coordinates (place images in reasonable positions)
                    image_index = len(image_chunks)
                    y_pos = 0.1 + (image_index * 0.15)  # Spread images vertically
                    if y_pos > 0.8:  # Reset if too far down
                        y_pos = 0.1 + ((image_index % 5) * 0.15)

                    # Estimate size based on image data length
                    data_size = len(image_data)
                    if data_size < 50000:  # Small image
                        width, height = 0.2, 0.1
                    elif data_size < 200000:  # Medium image
                        width, height = 0.3, 0.2
                    else:  # Large image
                        width, height = 0.4, 0.3

                    # Create image chunk
                    chunk = DocumentChunk(
                        doc_id="",
                        page=1,
                        x=0.1,  # Left margin
                        y=y_pos,
                        w=width,
                        h=height,
                        type=ContentType.IMAGE,
                        text=None,
                        tokens=None,
                        binary_data=binary_data,
                        metadata={
                            **document_metadata,
                            "image_format": image_format,
                            "image_size_bytes": len(image_data),
                            "original_path": media_path,
                            "extraction_method": "docx_stdlib"
                        }
                    )
                    image_chunks.append(chunk)

                except Exception as img_error:
                    logger.debug(f"Error extracting image {media_path}: {img_error}")
                    continue

            logger.debug(f"Extracted {len(image_chunks)} images from DOCX")

        except Exception as e:
            logger.debug(f"Error extracting images from DOCX: {e}")

        return image_chunks

    @property
    def supported_extensions(self) -> list[str]:
        """Return supported file extensions."""
        return [".docx", ".docm"]