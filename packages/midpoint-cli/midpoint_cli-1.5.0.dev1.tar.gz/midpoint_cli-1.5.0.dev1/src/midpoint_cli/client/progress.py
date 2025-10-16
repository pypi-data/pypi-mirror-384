from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional


class ProgressMonitor(ABC):
    """Abstract base class for task progress monitors."""

    @abstractmethod
    def update(self, progress: int) -> None:
        """Update the progress display with the current progress value."""
        pass

    def update_with_stats(self, progress: int, success_count: int = 0, failure_count: int = 0) -> None:  # noqa: B027
        """
        Update the progress display with current progress and success/failure statistics.

        This is an optional method that implementations can override to display
        detailed statistics. Default implementation falls back to simple update().

        Args:
            progress: Current progress value (total items processed)
            success_count: Number of successfully processed items
            failure_count: Number of failed items
        """
        self.update(progress)

    def set_task_start_time(self, start_time: Optional[datetime]) -> None:  # noqa: B027
        """
        Set the task's original start time for elapsed time calculation.

        This allows the progress monitor to show elapsed time from when the task
        originally started, not from when monitoring began. Optional method that
        implementations can override if they support elapsed time display.

        Args:
            start_time: The datetime when the task originally started, or None
        """
        ...

    @abstractmethod
    def __enter__(self):
        """Enter context manager."""
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        pass


class NopProgressMonitor(ProgressMonitor):
    """No-op implementation."""

    def update(self, progress: int) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
