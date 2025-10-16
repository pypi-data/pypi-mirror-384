"""
Pipeline implementation for the docpipe document processing pipeline.

This module provides the PipelineMixin class that orchestrates the complete
document processing workflow from loading to formatting.
"""

from __future__ import annotations

import logging
from typing import Iterable, Optional, Any, Union, Callable
from typing_extensions import Self

from ._types import (
    IOStream, FormattedOutput, ProcessingMetadata,
    TypedStream, PageStream, BlockStream, TableStream, ImageStream,
    detect_stream_type
)
from ._protocols import (
    LoaderProtocol,
    ProcessorProtocol,
    FormatterProtocol,
    PipelineProtocol
)

logger = logging.getLogger(__name__)


class PipelineMixin(PipelineProtocol):
    """
    Mixin class for document processing pipelines.

    Provides orchestration for the complete document processing workflow:
    1. Document loading from various formats
    2. Content processing and structuring
    3. Output formatting for storage or transmission

    Features:
    - Pluggable component registry
    - Automatic component selection
    - Memory management and monitoring
    - Error handling and recovery
    - Processing metadata tracking
    """

    def __init__(self, *, max_mem_mb: Optional[int] = None):
        """
        Initialize the pipeline with optional memory limits.

        Args:
            max_mem_mb: Default memory limit in MB for processing
        """
        self.default_max_mem_mb = max_mem_mb
        self._loaders: list[LoaderProtocol] = []
        self._processors: list[ProcessorProtocol[Any, Any]] = []
        self._formatters: list[FormatterProtocol] = []

    # Component registry methods

    def add_loader(self, loader: LoaderProtocol) -> Self:
        """
        Add a document loader to the pipeline registry.

        Args:
            loader: The loader to add

        Returns:
            Self for method chaining
        """
        self._loaders.append(loader)
        logger.debug(f"Added loader: {loader.__class__.__name__}")
        return self

    def add_processor(self, processor: ProcessorProtocol[Any, Any]) -> Self:
        """
        Add an object processor to the pipeline registry.

        Args:
            processor: The processor to add

        Returns:
            Self for method chaining
        """
        self._processors.append(processor)
        logger.debug(f"Added processor: {processor.__class__.__name__}")
        return self

    def add_formatter(self, formatter: FormatterProtocol) -> Self:
        """
        Add a formatter to the pipeline registry.

        Args:
            formatter: The formatter to add

        Returns:
            Self for method chaining
        """
        self._formatters.append(formatter)
        logger.debug(f"Added formatter: {formatter.__class__.__name__}")
        return self

    # Component selection methods

    def _select_loader(self, source: Union[str, IOStream]) -> LoaderProtocol:
        """
        Select the appropriate loader for the given source.

        Args:
            source: The document source

        Returns:
            Selected loader instance

        Raises:
            ValueError: If no suitable loader is found
        """
        for loader in self._loaders:
            if loader.can_load(source):
                logger.debug(f"Selected loader: {loader.__class__.__name__}")
                return loader

        raise ValueError(f"No loader found for source: {source}")

    def _select_processor(self, stream: TypedStream) -> Optional[ProcessorProtocol[Any, Any]]:
        """
        Select the appropriate processor for the given typed stream.

        Args:
            stream: The typed stream

        Returns:
            Selected processor or None if no suitable processor found
        """
        for processor in self._processors:
            if processor.can_process(stream):
                logger.debug(f"Selected processor: {processor.__class__.__name__}")
                return processor

        logger.debug(f"No processor found for stream type: {type(stream).__name__}")
        return None

    def _select_formatter(self, data: Any, format_name: str) -> FormatterProtocol:
        """
        Select the appropriate formatter for the given data and format.

        Args:
            data: The data to format
            format_name: The target format name

        Returns:
            Selected formatter instance

        Raises:
            ValueError: If no suitable formatter is found
        """
        for formatter in self._formatters:
            if formatter.can_format(data, format_name):
                logger.debug(f"Selected formatter: {formatter.__class__.__name__}")
                return formatter

        raise ValueError(f"No formatter found for format: {format_name}")

    # Processing pipeline methods

    def process(
        self,
        source: Union[str, IOStream],
        *,
        loader: Optional[LoaderProtocol] = None,
        processor: Optional[ProcessorProtocol[Any, Any]] = None,
        formatter: Optional[FormatterProtocol] = None,
        format_name: str = "markdown",
        max_mem_mb: Optional[int] = None,
        **metadata: Any
    ) -> Iterable[FormattedOutput]:
        """
        Process a document through the complete pipeline.

        Args:
            source: The document source
            loader: Optional custom loader
            processor: Optional custom processor
            formatter: Optional custom formatter
            format_name: Target output format
            max_mem_mb: Memory limit for processing
            **metadata: Additional processing metadata

        Yields:
            Formatted output results as IO[bytes]
        """
        max_mem = max_mem_mb or self.default_max_mem_mb

        logger.info(f"Starting pipeline processing for source: {source}")

        try:
            # Stage 1: Document Loading
            logger.debug("Stage 1: Document loading")
            selected_loader = loader or self._select_loader(source)

            # Add pipeline metadata
            processing_metadata = self._create_pipeline_metadata(
                source, selected_loader, format_name, **metadata
            )

            # Load document content as streams
            content_streams = list(selected_loader.load(
                source,
                max_mem_mb=max_mem,
                **processing_metadata
            ))

            logger.info(f"Loaded {len(content_streams)} content streams")

            # Stage 2: Object Processing (optional)
            logger.debug("Stage 2: Object processing")
            processed_objects = []

            for i, stream in enumerate(content_streams):
                # Ensure stream is a TypedStream
                if not isinstance(stream, (PageStream, BlockStream, TableStream, ImageStream)):
                    logger.warning(f"Skipping non-typed stream: {type(stream)}")
                    continue

                # Use provided processor or auto-select based on stream type
                selected_processor = processor or self._select_processor(stream)

                if selected_processor:
                    # Process the content with type safety
                    processed_result = selected_processor.process(
                        stream,
                        max_mem_mb=max_mem,
                        **processing_metadata
                    )
                    processed_objects.append(processed_result)
                    logger.debug(f"Processed stream {i+1} ({type(stream).__name__}) with {selected_processor.__class__.__name__}")
                else:
                    # No processor available, keep original stream
                    processed_objects.append(stream)
                    logger.debug(f"No processor for stream {i+1} ({type(stream).__name__}), keeping original")

            # Stage 3: Formatting
            logger.debug("Stage 3: Formatting")
            selected_formatter = formatter or self._select_formatter(
                processed_objects[0] if processed_objects else None,
                format_name
            )

            # Format each processed object
            for i, obj in enumerate(processed_objects):
                try:
                    formatted_output = selected_formatter.format(
                        obj,
                        format_name,
                        max_mem_mb=max_mem,
                        **processing_metadata
                    )
                    yield formatted_output
                    logger.debug(f"Formatted object {i+1} as {format_name}")

                except Exception as e:
                    logger.error(f"Error formatting object {i+1}: {e}")
                    # Continue with other objects instead of failing completely
                    continue

            logger.info(f"Pipeline processing completed for source: {source}")

        except Exception as e:
            logger.error(f"Pipeline processing failed: {e}")
            raise

    def get_supported_formats(self) -> dict[str, list[str]]:
        """
        Get all supported formats across registered components.

        Returns:
            Dictionary mapping component types to supported formats
        """
        return {
            "loaders": [fmt for loader in self._loaders for fmt in loader.supported_formats],
            "processors": [
                f"{processor.input_type.__name__} -> {processor.output_type.__name__}"
                for processor in self._processors
            ],
            "formatters": [fmt for formatter in self._formatters for fmt in formatter.supported_formats],
        }

    def _create_pipeline_metadata(
        self,
        source: Union[str, IOStream],
        loader: LoaderProtocol,
        format_name: str,
        **extra: Any
    ) -> ProcessingMetadata:
        """
        Create processing metadata for the pipeline execution.

        Args:
            source: The document source
            loader: Selected loader
            format_name: Target format name
            **extra: Additional metadata fields

        Returns:
            Processing metadata dictionary
        """
        metadata: ProcessingMetadata = {
            "pipeline_type": self.__class__.__name__,
            "loader_type": loader.__class__.__name__,
            "target_format": format_name,
            "max_mem_mb": self.default_max_mem_mb,
            "loaders_count": len(self._loaders),
            "processors_count": len(self._processors),
            "formatters_count": len(self._formatters),
        }

        metadata.update(extra)
        return metadata

    # Utility methods

    def get_supported_formats(self) -> dict[str, list[str]]:
        """
        Get all supported formats across registered components.

        Returns:
            Dictionary mapping component types to supported formats
        """
        return {
            "loaders": [fmt for loader in self._loaders for fmt in loader.supported_formats],
            "processors": [proc_type for processor in self._processors for proc_type in processor.supported_types],
            "formatters": [fmt for formatter in self._formatters for fmt in formatter.supported_formats],
        }

    def clear_registry(self) -> Self:
        """
        Clear all registered components.

        Returns:
            Self for method chaining
        """
        self._loaders.clear()
        self._processors.clear()
        self._formatters.clear()
        logger.debug("Cleared all component registries")
        return self

    def __len__(self) -> int:
        """Return total number of registered components."""
        return len(self._loaders) + len(self._processors) + len(self._formatters)

    def __repr__(self) -> str:
        """String representation of the pipeline."""
        return (
            f"{self.__class__.__name__}("
            f"loaders={len(self._loaders)}, "
            f"processors={len(self._processors)}, "
            f"formatters={len(self._formatters)})"
        )


class SimplePipeline(PipelineMixin):
    """
    A simple pipeline implementation with basic defaults.

    This is a convenience class that provides a ready-to-use pipeline
    with sensible defaults for common document processing tasks.
    """

    def __init__(self, *, max_mem_mb: Optional[int] = 512):
        """
        Initialize a simple pipeline with default memory limit.

        Args:
            max_mem_mb: Default memory limit in MB (default: 512)
        """
        super().__init__(max_mem_mb=max_mem_mb)

    def auto_configure(self) -> Self:
        """
        Auto-configure the pipeline with available components.

        This method will scan for available components and register them
        automatically based on their capabilities.

        Returns:
            Self for method chaining
        """
        # This would be implemented to auto-discover and register components
        # For now, it's a placeholder for future enhancement
        logger.info("Auto-configuration not yet implemented")
        return self