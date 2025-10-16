"""
CLI interface for docpipe-mini.

Optional dependency - provides rich command-line interface.
"""

try:
    from ._typer import main, app
    CLI_AVAILABLE = True
except ImportError:
    CLI_AVAILABLE = False

    def main():
        """Fallback when typer is not available."""
        import sys
        print("Error: typer and rich are required for the CLI interface.")
        print("Install with: pip install 'docpipe-mini[cli]'")
        sys.exit(1)

__all__ = ["main", "CLI_AVAILABLE"]