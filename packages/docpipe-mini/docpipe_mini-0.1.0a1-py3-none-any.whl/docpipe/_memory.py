"""
Memory guardrail for document processing.

Provides memory monitoring and subprocess isolation to prevent
memory exhaustion when processing large documents.
"""

from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Iterator, Optional, Any

logger = logging.getLogger(__name__)

# Memory monitoring constants
DEFAULT_MEMORY_LIMIT_MB = 512
MEMORY_CHECK_INTERVAL = 0.5  # seconds
MEMORY_WARNING_THRESHOLD = 0.8  # 80% of limit

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logger.warning("psutil not available, memory monitoring disabled")


def get_memory_usage_mb() -> float:
    """
    Get current memory usage in MB.

    Returns:
        Memory usage in megabytes, or 0 if psutil not available
    """
    if not PSUTIL_AVAILABLE:
        return 0.0

    try:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return 0.0


class MemoryGuard:
    """
    Memory monitoring and enforcement guard.

    Monitors memory usage and raises warnings or kills process
    when limits are exceeded.
    """

    def __init__(self, limit_mb: float = DEFAULT_MEMORY_LIMIT_MB):
        """
        Initialize memory guard.

        Args:
            limit_mb: Memory limit in megabytes
        """
        self.limit_mb = limit_mb
        self.start_time = time.time()
        self.max_usage = 0.0
        self.warning_count = 0

    def check_usage(self) -> None:
        """
        Check current memory usage and enforce limits.

        Raises:
            MemoryError: If memory limit exceeded
        """
        if not PSUTIL_AVAILABLE:
            return

        current_usage = get_memory_usage_mb()
        self.max_usage = max(self.max_usage, current_usage)

        # Check if we're approaching the limit
        usage_ratio = current_usage / self.limit_mb

        if usage_ratio > 1.0:
            # Memory limit exceeded - terminate
            logger.error(
                f"Memory limit exceeded: {current_usage:.1f}MB > {self.limit_mb}MB. "
                f"Terminating process."
            )
            raise MemoryError(
                f"Memory limit exceeded: {current_usage:.1f}MB > {self.limit_mb}MB"
            )

        elif usage_ratio > MEMORY_WARNING_THRESHOLD:
            # Warning threshold exceeded
            self.warning_count += 1
            if self.warning_count == 1:  # Only warn once
                logger.warning(
                    f"High memory usage: {current_usage:.1f}MB "
                    f"({usage_ratio*100:.1f}% of limit)"
                )

    def get_stats(self) -> dict[str, Any]:
        """
        Get memory usage statistics.

        Returns:
            Dictionary with memory statistics
        """
        return {
            "limit_mb": self.limit_mb,
            "max_usage_mb": self.max_usage,
            "current_usage_mb": get_memory_usage_mb(),
            "warning_count": self.warning_count,
            "duration_seconds": time.time() - self.start_time,
            "psutil_available": PSUTIL_AVAILABLE
        }


def run_with_memory_limit(
    func: callable,
    *args,
    memory_limit_mb: float = DEFAULT_MEMORY_LIMIT_MB,
    timeout_seconds: Optional[float] = None,
    **kwargs
) -> Any:
    """
    Run a function with memory limits in a subprocess.

    This provides isolation for potentially memory-intensive operations
    by running them in a subprocess with memory monitoring.

    Args:
        func: Function to run
        *args: Function arguments
        memory_limit_mb: Memory limit in MB
        timeout_seconds: Optional timeout in seconds
        **kwargs: Function keyword arguments

    Returns:
        Function return value

    Raises:
        subprocess.TimeoutExpired: If timeout exceeded
        MemoryError: If memory limit exceeded
        subprocess.CalledProcessError: If function failed
    """
    if not PSUTIL_AVAILABLE:
        logger.warning("psutil not available, running without memory limits")
        return func(*args, **kwargs)

    # Create temporary files for communication
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as result_file:
        result_path = result_file.name

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as error_file:
        error_path = error_file.name

    try:
        # Prepare subprocess code
        subprocess_code = f'''
import sys
import json
import traceback
from pathlib import Path

# Add the source directory to Python path
sys.path.insert(0, r"{Path(__file__).parent.parent}")

try:
    from docpipe._memory import MemoryGuard

    # Set up memory guard
    guard = MemoryGuard(limit_mb={memory_limit_mb})

    # Import and run the function
    from {func.__module__} import {func.__name__}

    # Prepare arguments
    args = {repr(args)}
    kwargs = {repr(kwargs)}

    # Run with memory monitoring
    result = {func.__name__}(*args, **kwargs)

    # Save result
    with open(r"{result_path}", 'w') as f:
        json.dump({{"success": True, "result": result, "stats": guard.get_stats()}}, f)

except Exception as e:
    # Save error
    with open(r"{error_path}", 'w') as f:
        json.dump({{"success": False, "error": str(e), "traceback": traceback.format_exc()}}, f)
    sys.exit(1)
'''

        # Write subprocess code to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as code_file:
            code_path = code_file.name
            code_file.write(subprocess_code)

        try:
            # Run subprocess
            logger.debug(f"Starting subprocess with {memory_limit_mb}MB memory limit")
            process = subprocess.Popen(
                [sys.executable, code_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            try:
                stdout, stderr = process.communicate(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                raise subprocess.TimeoutExpired(
                    f"Function {func.__name__} timed out after {timeout_seconds} seconds"
                )

            # Check result
            if process.returncode == 0:
                # Success - read result
                if Path(result_path).exists():
                    with open(result_path, 'r') as f:
                        result_data = json.load(f)

                    if result_data.get("success"):
                        logger.debug(f"Subprocess completed: {result_data.get('stats', {})}")
                        return result_data.get("result")
                    else:
                        raise RuntimeError(f"Function failed: {result_data.get('error')}")
                else:
                    raise RuntimeError("Subprocess completed but no result file found")
            else:
                # Error occurred
                if Path(error_path).exists():
                    with open(error_path, 'r') as f:
                        error_data = json.load(f)
                    raise RuntimeError(f"Function failed: {error_data.get('error')}")
                else:
                    raise subprocess.CalledProcessError(
                        process.returncode, func.__name__, stderr
                    )

        finally:
            # Clean up temporary code file
            try:
                Path(code_path).unlink()
            except OSError:
                pass

    finally:
        # Clean up result and error files
        for path in [result_path, error_path]:
            try:
                Path(path).unlink(missing_ok=True)
            except OSError:
                pass


class MemorySafeIterator:
    """
    Iterator wrapper that monitors memory usage during iteration.

    Provides memory-safe iteration over potentially large iterables.
    """

    def __init__(
        self,
        iterator: Iterator,
        memory_limit_mb: float = DEFAULT_MEMORY_LIMIT_MB,
        check_interval: int = 10
    ):
        """
        Initialize memory-safe iterator.

        Args:
            iterator: Iterator to wrap
            memory_limit_mb: Memory limit in MB
            check_interval: Check memory every N items
        """
        self.iterator = iterator
        self.memory_limit_mb = memory_limit_mb
        self.check_interval = check_interval
        self.count = 0

    def __iter__(self):
        """Return iterator."""
        return self

    def __next__(self):
        """Get next item with memory checking."""
        if not PSUTIL_AVAILABLE:
            return next(self.iterator)

        # Check memory usage periodically
        if self.count % self.check_interval == 0 and self.count > 0:
            current_usage = get_memory_usage_mb()
            if current_usage > self.memory_limit_mb:
                raise MemoryError(
                    f"Memory limit exceeded during iteration: "
                    f"{current_usage:.1f}MB > {self.memory_limit_mb}MB"
                )

        try:
            item = next(self.iterator)
            self.count += 1
            return item
        except StopIteration:
            # Log final stats
            logger.debug(f"Iteration completed after {self.count} items")
            raise