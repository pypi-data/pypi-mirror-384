"""
CLI interface for docpipe-mini using Typer.

Optional dependency - provides rich command-line interface with
progress bars, error handling, and formatting options.
"""

from __future__ import annotations

import base64
import logging
import sys
import time
import json
from pathlib import Path
from typing import Optional

try:
    import typer
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.table import Table
    from rich.text import Text
    TYPER_AVAILABLE = True
except ImportError:
    TYPER_AVAILABLE = False

from .. import serialize, serialize_to_jsonl, list_formats
from .._memory import MemoryGuard, get_memory_usage_mb

def _format_chunk_for_console(chunk) -> str:
    """
    Format chunk for console display with truncated binary data.

    Args:
        chunk: DocumentChunk to format

    Returns:
        Formatted JSON string suitable for console display
    """
    chunk_dict = chunk.to_dict()

    # Truncate binary data for console display
    if chunk_dict.get("binary_data") and isinstance(chunk_dict["binary_data"], str):
        binary_data = chunk_dict["binary_data"]
        if len(binary_data) > 50:
            chunk_dict["binary_data"] = binary_data[:50] + "..."
            chunk_dict["truncated"] = True
            chunk_dict["original_size"] = len(binary_data)

    return json.dumps(chunk_dict, ensure_ascii=False)

if TYPER_AVAILABLE:
    app = typer.Typer(
        name="docpipe-mini",
        help="Minimal document-to-jsonl serializer with coordinates for AI",
        no_args_is_help=True,
        rich_markup_mode="rich"
    )

    console = Console()

    @app.command()
    def serialize_cmd(
        input_file: Path = typer.Argument(
            ...,
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            help="Document file to serialize"
        ),
        output_file: Optional[Path] = typer.Option(
            None,
            "-o",
            "--output",
            help="Output file (default: stdout)"
        ),
        max_mem_mb: int = typer.Option(
            512,
            "--max-mem",
            help="Memory limit in MB",
            show_default=True
        ),
        doc_id: Optional[str] = typer.Option(
            None,
            "--doc-id",
            help="Custom document ID (default: auto-generated)"
        ),
        verbose: bool = typer.Option(
            False,
            "-v",
            "--verbose",
            help="Enable verbose logging"
        ),
        jsonl: bool = typer.Option(
            True,
            "--jsonl/--no-jsonl",
            help="Output JSONL format (default: true)"
        ),
        stats: bool = typer.Option(
            False,
            "--stats",
            help="Show processing statistics"
        ),
        include_binary: bool = typer.Option(
            False,
            "--include-binary",
            help="Include binary data (images) in JSON output (base64 encoded)"
        ),
        content_types: Optional[str] = typer.Option(
            None,
            "--types",
            help="Filter by content types (comma-separated: text,table,image)"
        ),
        export_images: Optional[Path] = typer.Option(
            None,
            "--export-images",
            help="Export images to directory (requires --include-binary)"
        )
    ) -> None:
        """
        Serialize a document to JSONL format with coordinates.

        Examples:
            docpipe-mini document.pdf
            docpipe-mini document.pdf -o output.jsonl
            docpipe-mini document.docx --max-mem 256 --stats
            docpipe-mini document.pdf --types text,table  # Filter content types
            docpipe-mini document.pdf --include-binary --stats  # Include binary data
            docpipe-mini document.pdf --export-images ./images  # Export images
        """
        # Setup logging
        if verbose:
            logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
        else:
            logging.basicConfig(level=logging.WARNING)

        # Validate input
        if not input_file.exists():
            console.print(f"[red]Error: Input file not found: {input_file}[/red]")
            raise typer.Exit(1)

        # Parse content types filter
        content_filter = None
        if content_types:
            content_filter = [t.strip().lower() for t in content_types.split(',') if t.strip()]
            console.print(f"[blue]Content filter:[/blue] {', '.join(content_filter)}")

        # Validate export images option
        if export_images and not include_binary:
            console.print("[yellow]Warning: --export-images requires --include-binary, enabling automatically[/yellow]")
            include_binary = True

        # Create export directory if needed
        if export_images:
            export_images.mkdir(parents=True, exist_ok=True)
            console.print(f"[blue]Export directory:[/blue] {export_images}")

        # Start processing
        start_time = time.time()
        memory_guard = MemoryGuard(limit_mb=max_mem_mb)

        console.print(f"[blue]Processing:[/blue] {input_file}")
        console.print(f"[blue]Memory limit:[/blue] {max_mem_mb} MB")
        console.print(f"[blue]Binary data:[/blue] {'Enabled' if include_binary else 'Disabled'}")

        try:
            # Count chunks for progress bar
            if verbose:
                console.print("[yellow]Counting chunks...[/yellow]")
                chunk_count = sum(1 for _ in serialize(input_file, max_mem_mb=max_mem_mb))
                console.print(f"[green]Found {chunk_count} chunks[/green]")
            else:
                chunk_count = None

            # Track processing statistics
            type_counts = {}
            binary_count = 0
            image_export_count = 0

            # Process with progress bar
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:

                task = progress.add_task(
                    "Serializing document...",
                    total=chunk_count
                )

                # Create iterator
                chunk_iterator = serialize(input_file, max_mem_mb=max_mem_mb, doc_id=doc_id)

                # Apply content type filtering if specified
                if content_filter:
                    def filtered_iterator(source_iterator):
                        for chunk in source_iterator:
                            if chunk.type.lower() in content_filter:
                                yield chunk

                    chunk_iterator = filtered_iterator(chunk_iterator)

                # Open output file or use stdout
                if output_file:
                    output_path = Path(output_file)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        for i, chunk in enumerate(chunk_iterator):
                            # Update type counts
                            chunk_type = chunk.type
                            type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1

                            # Handle binary data
                            if include_binary and chunk.binary_data:
                                binary_count += 1

                            # Export images
                            if export_images and chunk.type == 'image' and chunk.binary_data:
                                _export_image(chunk, export_images, i)
                                image_export_count += 1

                            # Write output
                            if jsonl:
                                f.write(chunk.to_jsonl() + '\n')
                            else:
                                f.write(f"{chunk}\n")

                            # Update progress
                            if chunk_count:
                                progress.update(task, advance=1)
                            memory_guard.check_usage()
                else:
                    # Write to stdout
                    for i, chunk in enumerate(chunk_iterator):
                        # Update type counts
                        chunk_type = chunk.type
                        type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1

                        # Handle binary data
                        if include_binary and chunk.binary_data:
                            binary_count += 1

                        # Export images
                        if export_images and chunk.type == 'image' and chunk.binary_data:
                            _export_image(chunk, export_images, i)
                            image_export_count += 1

                        # Write output
                        if jsonl:
                            print(_format_chunk_for_console(chunk))
                        else:
                            print(chunk)

                        # Update progress
                        if chunk_count:
                            progress.update(task, advance=1)
                        memory_guard.check_usage()

            # Show statistics
            end_time = time.time()
            duration = end_time - start_time
            stats_data = memory_guard.get_stats()

            if stats:
                console.print("\n[green]SUCCESS: Processing completed[/green]")

                stats_table = Table(title="Processing Statistics")
                stats_table.add_column("Metric", style="cyan")
                stats_table.add_column("Value", style="magenta")

                stats_table.add_row("Duration", f"{duration:.2f} seconds")
                stats_table.add_row("Memory Used", f"{stats_data['max_usage_mb']:.1f} MB")
                stats_table.add_row("Memory Limit", f"{stats_data['limit_mb']:.1f} MB")
                stats_table.add_row("Chunks Processed", str(chunk_count or "Unknown"))
                stats_table.add_row("Warnings", str(stats_data['warning_count']))

                # Add content type statistics
                if type_counts:
                    console.print("\n[blue]Content Type Breakdown:[/blue]")
                    for content_type, count in sorted(type_counts.items()):
                        console.print(f"  {content_type}: {count}")

                # Add IO object statistics
                if include_binary:
                    console.print(f"\n[blue]IO Objects:[/blue]")
                    console.print(f"  Binary data chunks: {binary_count}")
                    if export_images:
                        console.print(f"  Images exported: {image_export_count}")

                console.print(stats_table)

        except KeyboardInterrupt:
            console.print("\n[yellow]WARNING: Processing interrupted by user[/yellow]")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"\n[red]ERROR: {e}[/red]")
            if verbose:
                console.print_exception()
            raise typer.Exit(1)

    @app.command()
    def formats() -> None:
        """List supported document formats."""
        formats = list_formats()

        if not formats:
            console.print("[yellow]No serializers registered[/yellow]")
            return

        table = Table(title="Supported Document Formats")
        table.add_column("Serializer", style="cyan")
        table.add_column("Extensions", style="green")

        for serializer_name, extensions in formats.items():
            ext_str = ", ".join(extensions)
            table.add_row(serializer_name, ext_str)

        console.print(table)

    @app.command()
    def info() -> None:
        """Show system information."""
        from .. import __version__

        info_table = Table(title="System Information")
        info_table.add_column("Property", style="cyan")
        info_table.add_column("Value", style="magenta")

        info_table.add_row("Version", __version__)
        info_table.add_row("Python", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        info_table.add_row("Platform", sys.platform)
        info_table.add_row("psutil Available", "Yes" if get_memory_usage_mb() > 0 else "No")
        info_table.add_row("Current Memory", f"{get_memory_usage_mb():.1f} MB")

        console.print(info_table)

        console.print("\n[blue]Environment Variables:[/blue]")
        console.print("  DOPIPE_DEBUG: Enable debug logging")
        console.print("  DOPIPE_MEMORY_MB: Default memory limit")

    @app.command()
    def validate(
        input_file: Path = typer.Argument(
            ...,
            exists=True,
            help="Document file to validate"
        )
    ) -> None:
        """
        Validate a document file without full processing.

        Checks if the file can be parsed and shows basic information.
        """
        console.print(f"[blue]Validating:[/blue] {input_file}")

        try:
            # Quick validation
            start_time = time.time()
            chunk_count = 0
            sample_chunks = []

            for i, chunk in enumerate(serialize(input_file)):
                chunk_count += 1
                if i < 3:  # Collect first 3 chunks as sample
                    sample_chunks.append(chunk)
                if i >= 10:  # Don't process too many for validation
                    break

            duration = time.time() - start_time

            console.print(f"[green]PASS: Validation passed[/green]")
            console.print(f"- File type: {input_file.suffix}")
            console.print(f"- Sample chunks: {len(sample_chunks)}")
            console.print(f"- Estimated total: {chunk_count}+ chunks")
            console.print(f"- Processing speed: {duration:.2f}s for sample")

            if sample_chunks:
                console.print("\n[blue]Sample chunks:[/blue]")
                for i, chunk in enumerate(sample_chunks):
                    preview = (chunk.text or "")[:50] + "..." if len(chunk.text or "") > 50 else (chunk.text or "")
                    console.print(f"  {i+1}. [{chunk.type}] {preview} (tokens: {chunk.tokens})")

        except Exception as e:
            console.print(f"[red]ERROR: Validation failed: {e}[/red]")
            raise typer.Exit(1)

    def _export_image(chunk, export_dir: Path, index: int) -> None:
        """
        Export image chunk to file.

        Args:
            chunk: DocumentChunk with image data
            export_dir: Directory to export to
            index: Image index for filename
        """
        if not chunk.binary_data or chunk.type != 'image':
            return

        try:
            # Decode base64 data
            image_bytes = base64.b64decode(chunk.binary_data)

            # Generate filename
            filename = f"image_page{chunk.page}_{index:04d}.png"
            image_path = export_dir / filename

            # Write image file
            with open(image_path, 'wb') as f:
                f.write(image_bytes)

        except Exception as e:
            console.print(f"[yellow]Warning: Could not export image {index}: {e}[/yellow]")

else:
    # Fallback CLI when typer is not available
    def cli_fallback():
        """Fallback CLI when typer is not available."""
        print("Error: typer and rich are required for the CLI interface.")
        print("Install with: pip install docpipe-mini[cli]")
        print("Or use the Python API directly:")
        print("  import docpipe_mini as dp")
        print("  for chunk in dp.serialize('document.pdf'):")
        print("      print(chunk.to_jsonl())")
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    if TYPER_AVAILABLE:
        app()
    else:
        cli_fallback()


if __name__ == "__main__":
    main()