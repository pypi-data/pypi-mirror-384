"""
Minimal protocols for docpipe document-to-jsonl serializer.

Focus: simple serialize() interface with zero dependency core.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator, Optional

from ._types import DocumentChunk


class DocumentSerializer(ABC):
    """
    Abstract base class for document serializers.

    This is the primary interface - all document processing flows through
    this simple, type-safe interface.
    """

    @abstractmethod
    def can_serialize(self, file_path: Path) -> bool:
        """
        Check if this serializer can handle the given file.

        Args:
            file_path: Path to the document file

        Returns:
            True if the file format is supported
        """
        ...

    @abstractmethod
    def serialize(
        self,
        file_path: Path,
        *,
        max_mem_mb: Optional[int] = None
    ) -> Iterator[DocumentChunk]:
        """
        Serialize document into coordinate-aware chunks.

        Args:
            file_path: Path to the document file
            max_mem_mb: Optional memory limit

        Yields:
            DocumentChunk objects with coordinates and text
        """
        ...

    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """List of supported file extensions."""
        ...


class SerializerRegistry:
    """
    Registry for document serializers with plugin support.
    """

    def __init__(self):
        self._serializers: list[DocumentSerializer] = []

    def register(self, serializer: DocumentSerializer) -> None:
        """Register a new serializer."""
        self._serializers.append(serializer)

    def get_serializer(self, file_path: Path) -> Optional[DocumentSerializer]:
        """Get appropriate serializer for file."""
        for serializer in self._serializers:
            if serializer.can_serialize(file_path):
                return serializer
        return None

    def list_supported_formats(self) -> dict[str, list[str]]:
        """Get all supported formats."""
        return {
            serializer.__class__.__name__: serializer.supported_extensions
            for serializer in self._serializers
        }


# Global registry instance
_registry = SerializerRegistry()


def get_serializer(file_path: Path) -> Optional[DocumentSerializer]:
    """Get serializer for file from global registry."""
    return _registry.get_serializer(file_path)


def register_serializer(serializer: DocumentSerializer) -> None:
    """Register serializer in global registry."""
    _registry.register(serializer)


def list_supported_formats() -> dict[str, list[str]]:
    """List all supported formats from global registry."""
    return _registry.list_supported_formats()