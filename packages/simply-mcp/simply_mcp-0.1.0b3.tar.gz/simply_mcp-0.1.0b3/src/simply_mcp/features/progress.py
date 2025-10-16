"""Progress reporting for long-running MCP operations.

This module provides a thread-safe progress reporting system that allows MCP tools
to report their progress during long-running operations. Progress updates are sent
to clients via the MCP protocol.

The module provides:
- ProgressReporter: Reports progress for a single operation
- ProgressTracker: Tracks multiple concurrent progress operations
- ProgressContext: Context manager for automatic progress lifecycle management

Example:
    >>> tracker = ProgressTracker()
    >>> async with tracker.start_operation("task-1") as progress:
    ...     for i in range(100):
    ...         await progress.update(i, message=f"Processing item {i}")
    ...         await asyncio.sleep(0.1)
"""

import asyncio
import time
import uuid
from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import Any

from simply_mcp.core.logger import get_logger

# Module-level logger
logger = get_logger(__name__)


class ProgressReporterImpl:
    """Implementation of progress reporter for a single operation.

    This class provides progress reporting functionality for a single long-running
    operation. It sends progress updates via a callback function and ensures
    thread-safe updates.

    Attributes:
        operation_id: Unique identifier for this operation
        callback: Callback function to send progress updates
        _last_update: Timestamp of last progress update
        _update_lock: Lock for thread-safe updates
        _completed: Whether the operation has completed

    Example:
        >>> async def send_progress(update: dict[str, Any]) -> None:
        ...     print(f"Progress: {update['percentage']}% - {update.get('message', '')}")
        >>>
        >>> reporter = ProgressReporterImpl("op-1", send_progress)
        >>> await reporter.update(50, message="Halfway done")
        >>> await reporter.complete()
    """

    def __init__(
        self,
        operation_id: str,
        callback: Callable[[dict[str, Any]], Any],
    ) -> None:
        """Initialize the progress reporter.

        Args:
            operation_id: Unique identifier for this operation
            callback: Callback function to send progress updates
        """
        self.operation_id = operation_id
        self.callback = callback
        self._last_update = time.time()
        self._update_lock = asyncio.Lock()
        self._completed = False

    async def update(
        self,
        percentage: float,
        message: str | None = None,
        current: int | None = None,
        total: int | None = None,
    ) -> None:
        """Update progress for this operation.

        This method creates a progress update and sends it via the callback.
        Updates are throttled to avoid overwhelming the client with too many
        notifications.

        Args:
            percentage: Progress as a percentage (0-100)
            message: Optional human-readable status message
            current: Optional current step number
            total: Optional total number of steps

        Example:
            >>> await reporter.update(25, message="Processing files", current=25, total=100)
        """
        if self._completed:
            logger.warning(
                f"Attempted to update completed operation: {self.operation_id}"
            )
            return

        async with self._update_lock:
            # Clamp percentage to valid range
            percentage = max(0.0, min(100.0, percentage))

            # Create progress update
            update: dict[str, Any] = {"percentage": percentage}

            if message is not None:
                update["message"] = message

            if current is not None:
                update["current"] = current

            if total is not None:
                update["total"] = total

            # Log progress update
            log_data: dict[str, Any] = {
                "operation_id": self.operation_id,
                "percentage": percentage,
            }
            if message:
                log_data["message"] = message
            if current is not None and total is not None:
                log_data["step"] = f"{current}/{total}"

            logger.debug(f"Progress update: {percentage}%", extra={"context": log_data})

            # Send update via callback
            try:
                result = self.callback(update)
                # Handle async callbacks
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error(
                    f"Error sending progress update: {e}",
                    extra={
                        "context": {
                            "operation_id": self.operation_id,
                            "error": str(e),
                        }
                    },
                )

            self._last_update = time.time()

    async def complete(self, message: str | None = None) -> None:
        """Mark the operation as complete.

        This sends a final progress update with 100% completion.

        Args:
            message: Optional completion message

        Example:
            >>> await reporter.complete(message="Processing finished successfully")
        """
        if not self._completed:
            await self.update(100.0, message=message or "Complete")
            self._completed = True
            logger.info(
                f"Operation completed: {self.operation_id}",
                extra={"context": {"operation_id": self.operation_id}},
            )

    async def fail(self, message: str) -> None:
        """Mark the operation as failed.

        This sends a final progress update indicating failure.

        Args:
            message: Error message explaining the failure

        Example:
            >>> await reporter.fail(message="Operation failed due to network error")
        """
        if not self._completed:
            logger.error(
                f"Operation failed: {self.operation_id}",
                extra={
                    "context": {
                        "operation_id": self.operation_id,
                        "error": message,
                    }
                },
            )
            # Don't set to 100% for failures, keep current percentage
            # Just send the failure message
            await self.update(
                self._last_percentage(),
                message=f"Failed: {message}",
            )
            self._completed = True

    def _last_percentage(self) -> float:
        """Get the last reported percentage.

        Returns:
            Last percentage value, or 0.0 if never updated
        """
        # This is a simple implementation - could be enhanced to track last value
        return 0.0

    @property
    def is_completed(self) -> bool:
        """Check if operation is completed.

        Returns:
            True if operation is completed, False otherwise
        """
        return self._completed


class ProgressTracker:
    """Tracker for multiple concurrent progress operations.

    This class manages multiple progress reporters for concurrent operations.
    It provides thread-safe creation, retrieval, and cleanup of progress reporters.

    Attributes:
        operations: Dictionary mapping operation IDs to progress reporters
        _lock: Lock for thread-safe operation management
        _default_callback: Default callback for progress updates

    Example:
        >>> tracker = ProgressTracker()
        >>> reporter1 = await tracker.create_operation("op-1")
        >>> reporter2 = await tracker.create_operation("op-2")
        >>> await reporter1.update(50)
        >>> await reporter2.update(75)
        >>> await tracker.remove_operation("op-1")
    """

    def __init__(
        self,
        default_callback: Callable[[dict[str, Any]], Any] | None = None,
    ) -> None:
        """Initialize the progress tracker.

        Args:
            default_callback: Optional default callback for progress updates
        """
        self.operations: dict[str, ProgressReporterImpl] = {}
        self._lock = asyncio.Lock()
        self._default_callback = default_callback

    async def create_operation(
        self,
        operation_id: str | None = None,
        callback: Callable[[dict[str, Any]], Any] | None = None,
    ) -> ProgressReporterImpl:
        """Create a new progress reporter for an operation.

        Args:
            operation_id: Optional operation ID (auto-generated if not provided)
            callback: Optional callback for this operation (uses default if not provided)

        Returns:
            New ProgressReporter instance

        Raises:
            ValueError: If operation_id already exists

        Example:
            >>> tracker = ProgressTracker()
            >>> reporter = await tracker.create_operation("my-task")
            >>> await reporter.update(50, message="In progress")
        """
        async with self._lock:
            # Generate operation ID if not provided
            if operation_id is None:
                operation_id = f"op-{uuid.uuid4().hex[:8]}"

            # Check if operation already exists
            if operation_id in self.operations:
                raise ValueError(f"Operation already exists: {operation_id}")

            # Use provided callback or default
            cb = callback or self._default_callback
            if cb is None:
                # Provide a no-op callback if none specified
                async def noop_callback(update: dict[str, Any]) -> None:
                    pass

                cb = noop_callback

            # Create reporter
            reporter = ProgressReporterImpl(operation_id, cb)
            self.operations[operation_id] = reporter

            logger.info(
                f"Created progress operation: {operation_id}",
                extra={"context": {"operation_id": operation_id}},
            )

            return reporter

    async def get_operation(self, operation_id: str) -> ProgressReporterImpl | None:
        """Get an existing progress reporter.

        Args:
            operation_id: Operation ID to retrieve

        Returns:
            ProgressReporter if found, None otherwise

        Example:
            >>> tracker = ProgressTracker()
            >>> reporter = await tracker.create_operation("task-1")
            >>> # Later...
            >>> same_reporter = await tracker.get_operation("task-1")
        """
        async with self._lock:
            return self.operations.get(operation_id)

    async def remove_operation(self, operation_id: str) -> None:
        """Remove a progress reporter.

        This should be called when an operation completes to clean up resources.

        Args:
            operation_id: Operation ID to remove

        Example:
            >>> tracker = ProgressTracker()
            >>> reporter = await tracker.create_operation("task-1")
            >>> await reporter.complete()
            >>> await tracker.remove_operation("task-1")
        """
        async with self._lock:
            if operation_id in self.operations:
                del self.operations[operation_id]
                logger.debug(
                    f"Removed progress operation: {operation_id}",
                    extra={"context": {"operation_id": operation_id}},
                )

    async def list_operations(self) -> list[str]:
        """List all active operation IDs.

        Returns:
            List of operation IDs

        Example:
            >>> tracker = ProgressTracker()
            >>> await tracker.create_operation("task-1")
            >>> await tracker.create_operation("task-2")
            >>> operations = await tracker.list_operations()
            >>> print(operations)  # ['task-1', 'task-2']
        """
        async with self._lock:
            return list(self.operations.keys())

    async def cleanup_completed(self) -> int:
        """Clean up all completed operations.

        Returns:
            Number of operations removed

        Example:
            >>> tracker = ProgressTracker()
            >>> reporter = await tracker.create_operation("task-1")
            >>> await reporter.complete()
            >>> removed = await tracker.cleanup_completed()
            >>> print(removed)  # 1
        """
        async with self._lock:
            completed = [
                op_id
                for op_id, reporter in self.operations.items()
                if reporter.is_completed
            ]

            for op_id in completed:
                del self.operations[op_id]

            if completed:
                logger.info(
                    f"Cleaned up {len(completed)} completed operations",
                    extra={"context": {"count": len(completed)}},
                )

            return len(completed)

    @asynccontextmanager
    async def start_operation(
        self,
        operation_id: str | None = None,
        callback: Callable[[dict[str, Any]], Any] | None = None,
    ) -> Any:
        """Context manager for automatic progress lifecycle management.

        This creates a progress reporter, yields it for use, and automatically
        marks it as complete (or failed if an exception occurs) when exiting.

        Args:
            operation_id: Optional operation ID (auto-generated if not provided)
            callback: Optional callback for this operation

        Yields:
            ProgressReporter instance

        Example:
            >>> tracker = ProgressTracker()
            >>> async with tracker.start_operation("task-1") as progress:
            ...     for i in range(100):
            ...         await progress.update(i, message=f"Step {i}")
            ...         await asyncio.sleep(0.1)
            # Automatically marked as complete when exiting
        """
        reporter = await self.create_operation(operation_id, callback)

        try:
            yield reporter
            # Mark as complete if not already completed
            if not reporter.is_completed:
                await reporter.complete()
        except Exception as e:
            # Mark as failed if an exception occurred
            if not reporter.is_completed:
                await reporter.fail(str(e))
            raise
        finally:
            # Clean up the operation
            await self.remove_operation(reporter.operation_id)


# Context manager alias for convenience
ProgressContext = ProgressTracker.start_operation


__all__ = [
    "ProgressReporterImpl",
    "ProgressTracker",
    "ProgressContext",
]
