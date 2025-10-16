import sys
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from rich.console import Console as RichConsole
from rich.panel import Panel
from rich.progress import BarColumn, Progress, ProgressColumn, SpinnerColumn, Task, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from midpoint_cli.client import MidpointCommunicationObserver
from midpoint_cli.client.progress import ProgressMonitor


def is_tty() -> bool:
    """Check if stdout is connected to a TTY (terminal)."""
    return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()


def _get_now_matching_timezone(reference_time: Optional[datetime]) -> datetime:
    """
    Get current time matching the timezone awareness of reference_time.

    Args:
        reference_time: A datetime to match timezone awareness with

    Returns:
        Current time as timezone-aware if reference is aware, naive otherwise
    """
    if reference_time is None:
        return datetime.utcnow()

    if reference_time.tzinfo is not None and reference_time.tzinfo.utcoffset(reference_time) is not None:
        # Reference is timezone-aware, return aware current time
        return datetime.now(timezone.utc)
    else:
        # Reference is naive, return naive current time
        return datetime.utcnow()


# Rich Console singleton
_console_instance: Optional[RichConsole] = None


def get_console() -> RichConsole:
    """Get or create the global Rich Console instance."""
    global _console_instance
    if _console_instance is None:
        custom_theme = Theme(
            {
                'info': 'cyan',
                'warning': 'yellow',
                'error': 'bold red',
                'success': 'bold green',
                'oid': 'blue',
                'name': 'bright_cyan',
                'status_running': 'yellow',
                'status_success': 'green',
                'status_error': 'red',
            }
        )
        _console_instance = RichConsole(theme=custom_theme, highlight=False)
    return _console_instance


def print_error(message: str) -> None:
    """Print an error message with rich formatting."""
    console = get_console()
    console.print(f'[error]Error:[/error] {message}')


def print_success(message: str) -> None:
    """Print a success message with rich formatting."""
    console = get_console()
    console.print(f'[success]✓[/success] {message}')


def print_info(message: str) -> None:
    """Print an info message with rich formatting."""
    console = get_console()
    console.print(f'[info]ℹ[/info] {message}')


def print_warning(message: str) -> None:
    """Print a warning message with rich formatting."""
    console = get_console()
    console.print(f'[warning]⚠[/warning] {message}')


def print_xml(xml_text: str, line_numbers: bool = False) -> None:
    """Print XML with syntax highlighting."""
    console = get_console()
    if is_tty():
        syntax = Syntax(xml_text, 'xml', theme='monokai', line_numbers=line_numbers)
        console.print(syntax)
    else:
        console.print(xml_text)


def create_table(title: Optional[str] = None, show_header: bool = True) -> Table:
    """Create a Rich table with consistent styling."""
    table = Table(title=title, show_header=show_header, header_style='bold cyan', border_style='blue')
    return table


def print_table_from_dicts(data: list[dict[str, Any]], title: Optional[str] = None) -> None:
    """Print a table from a list of dictionaries."""
    if not data:
        print_info('No data to display')
        return

    console = get_console()
    table = create_table(title=title)

    # Add columns from first dict
    headers = list(data[0].keys())
    for header in headers:
        table.add_column(header, style='white')

    # Add rows
    for row in data:
        table.add_row(*[str(row.get(h, '')) for h in headers])

    console.print(table)


def print_panel(content: str, title: Optional[str] = None, style: str = 'cyan') -> None:
    """Print content in a rich panel."""
    console = get_console()
    panel = Panel(content, title=title, border_style=style)
    console.print(panel)


class Spinner:
    """Reusable animated spinner using Rich for TTY/console output."""

    def __init__(self):
        self._console = get_console()
        self._status = None
        self._message = ''

    def start(self, message_callback: Callable[[str], str]):
        """
        Start spinner animation using Rich status.

        Args:
            message_callback: Function that receives spinner frame and returns full message to display
        """
        # Rich handles the spinner frame internally, so we just need the base message
        self._message = message_callback('')
        if is_tty():
            self._status = self._console.status(self._message, spinner='dots')
            self._status.__enter__()
        else:
            # For non-TTY, just print the message
            print(self._message, end='', flush=True)

    def stop(self, clear_length: int = 80):
        """
        Stop the spinner and clear the line.

        Args:
            clear_length: Number of characters to clear (default 80)
        """
        if self._status:
            self._status.__exit__(None, None, None)
            self._status = None
        elif not is_tty():
            # Clear the non-TTY message
            print('\r' + ' ' * clear_length + '\r', end='', flush=True)


class WaitingIndicator(ABC):
    """Abstract base class for waiting indicators."""

    @abstractmethod
    def start(self):
        """Start displaying the waiting indicator."""
        pass

    @abstractmethod
    def update(self):
        """Update the waiting indicator (called on each retry)."""
        pass

    @abstractmethod
    def stop(self):
        """Stop displaying the waiting indicator."""
        pass


class SpinnerWaitingIndicator(WaitingIndicator):
    """Animated spinner indicator for TTY/console output."""

    def __init__(self):
        self._spinner = Spinner()

    def start(self):
        """Start the animated spinner."""
        self._spinner.start(lambda frame: f'Waiting for http service {frame}')

    def update(self):
        """No-op: thread handles updates automatically."""
        pass

    def stop(self):
        """Stop the animated spinner and clear the line."""
        self._spinner.stop(clear_length=40)


class DottedWaitingIndicator(WaitingIndicator):
    """Classic dotted indicator for file redirection/non-TTY output."""

    def start(self):
        """Print initial waiting message."""
        print('Waiting for http service...', end='', flush=True)

    def update(self):
        """Print a dot on each update."""
        print('.', end='', flush=True)

    def stop(self):
        """Print newline to finish the line."""
        print('', flush=True)


class ConsoleDisplay(MidpointCommunicationObserver):
    def __init__(self):
        self._waiting = False
        # Detect if output is a TTY (console) or file redirection
        self._indicator = SpinnerWaitingIndicator() if is_tty() else DottedWaitingIndicator()

    def on_http_error(self):
        if not self._waiting:
            self._indicator.start()
            self._waiting = True
        else:
            self._indicator.update()

    def on_http_success(self):
        if self._waiting:
            self._indicator.stop()
            self._waiting = False

    def on_http_call(self):
        pass


# Progress Monitors


class CustomTimeElapsedColumn(ProgressColumn):
    """Custom time elapsed column that supports a start time offset."""

    def __init__(self, task_start_time: Optional[datetime] = None):
        super().__init__()
        self._task_start_time = task_start_time
        self._offset_seconds = 0.0
        if task_start_time:
            # Calculate how many seconds have elapsed since task started
            now = _get_now_matching_timezone(task_start_time)
            self._offset_seconds = (now - task_start_time).total_seconds()

    def render(self, task: Task) -> Text:
        """Render elapsed time including the offset from task start."""
        elapsed = task.finished_time if task.finished else task.elapsed
        if elapsed is None:
            elapsed = 0.0

        # Add the offset to show total time since task started
        total_elapsed = elapsed + self._offset_seconds

        # Format as hours:minutes:seconds
        hours, remainder = divmod(int(total_elapsed), 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            time_str = f'{hours:d}:{minutes:02d}:{seconds:02d}'
        else:
            time_str = f'{minutes:d}:{seconds:02d}'

        return Text(time_str, style='progress.elapsed')


class DottedProgressMonitor(ProgressMonitor):
    """Dotted progress monitor for file redirection/non-TTY output."""

    def __init__(self, width=80, icon='.'):
        self._progress = 0
        self._success_count = 0
        self._failure_count = 0
        self._width = width
        self._icon = icon
        self._task_start_time: Optional[datetime] = None
        self._start_time = time.time()

    def set_task_start_time(self, start_time: Optional[datetime]) -> None:
        """Set the task's original start time for elapsed time calculation."""
        self._task_start_time = start_time

    def update(self, progress: int) -> None:
        while self._progress < progress:
            self.advance()

    def update_with_stats(self, progress: int, success_count: int = 0, failure_count: int = 0) -> None:
        """Update with progress and success/failure statistics."""
        self._success_count = success_count
        self._failure_count = failure_count
        while self._progress < progress:
            self.advance()

    def advance(self):
        if self._progress % self._width == 0:
            if self._progress > 0:
                # Include stats in the progress line if available
                if self._success_count > 0 or self._failure_count > 0:
                    print(f' {self._progress:7d} (Success: {self._success_count}, Errors: {self._failure_count})')
                else:
                    print(f' {self._progress:7d}')

            print('Progress: ', end='', flush=True)

        print(self._icon, end='', flush=True)
        self._progress += 1

    def __enter__(self):
        self._start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print()
        # Build summary message with statistics if available
        if self._success_count > 0 or self._failure_count > 0:
            summary = (
                f'Total progress: {self._progress} (Success: {self._success_count}, Errors: {self._failure_count})'
            )
        else:
            summary = f'Total progress: {self._progress}'

        # Add elapsed time if we have a task start time
        if self._task_start_time:
            # Calculate total time since task started
            now = _get_now_matching_timezone(self._task_start_time)
            total_elapsed = (now - self._task_start_time).total_seconds()
            if self._success_count > 0 or self._failure_count > 0:
                summary = f'Total progress: {self._progress} (Success: {self._success_count}, Errors: {self._failure_count}, Task running for {self._format_elapsed(total_elapsed)})'
            else:
                summary = f'Total progress: {self._progress} (Task running for {self._format_elapsed(total_elapsed)})'

        print(summary)

    def _format_elapsed(self, seconds: float) -> str:
        """Format elapsed time as HH:MM:SS or MM:SS."""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, secs = divmod(remainder, 60)
        if hours > 0:
            return f'{hours:d}:{minutes:02d}:{secs:02d}'
        else:
            return f'{minutes:d}:{secs:02d}'


class AnimatedProgressMonitor(ProgressMonitor):
    """Animated progress monitor using Rich Progress for TTY/console output."""

    def __init__(self):
        self._progress_value = 0
        self._success_count = 0
        self._failure_count = 0
        self._progress = None
        self._task = None
        self._console = get_console()
        self._task_start_time: Optional[datetime] = None

    def set_task_start_time(self, start_time: Optional[datetime]) -> None:
        """Set the task's original start time for elapsed time calculation."""
        self._task_start_time = start_time

    def update(self, progress: int) -> None:
        self._progress_value = progress
        if self._progress and self._task is not None:
            self._progress.update(self._task, completed=progress)

    def update_with_stats(self, progress: int, success_count: int = 0, failure_count: int = 0) -> None:
        """Update with progress and success/failure statistics."""
        self._progress_value = progress
        self._success_count = success_count
        self._failure_count = failure_count
        if self._progress and self._task is not None:
            # Update description to show success/error breakdown
            if success_count > 0 or failure_count > 0:
                description = (
                    f'Processing... [green]Success: {success_count}[/green] [red]Errors: {failure_count}[/red]'
                )
            else:
                description = 'Processing...'
            self._progress.update(self._task, completed=progress, description=description)

    def __enter__(self):
        if is_tty():
            # Use custom elapsed column if we have a task start time
            time_column = CustomTimeElapsedColumn(self._task_start_time)

            self._progress = Progress(
                SpinnerColumn(),
                TextColumn('[progress.description]{task.description}'),
                BarColumn(),
                TextColumn('[progress.percentage]{task.completed}'),
                time_column,
                console=self._console,
            )
            self._progress.__enter__()
            self._task = self._progress.add_task('Processing...', total=None)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._progress:
            self._progress.__exit__(exc_type, exc_val, exc_tb)

        # Build summary message with statistics if available
        if self._success_count > 0 or self._failure_count > 0:
            summary = f'Total progress: {self._progress_value} ([green]Success: {self._success_count}[/green], [red]Errors: {self._failure_count}[/red])'
        else:
            summary = f'Total progress: {self._progress_value}'

        # Add elapsed time if we have a task start time
        if self._task_start_time:
            now = _get_now_matching_timezone(self._task_start_time)
            total_elapsed = (now - self._task_start_time).total_seconds()
            hours, remainder = divmod(int(total_elapsed), 3600)
            minutes, secs = divmod(remainder, 60)
            if hours > 0:
                time_str = f'{hours:d}:{minutes:02d}:{secs:02d}'
            else:
                time_str = f'{minutes:d}:{secs:02d}'
            summary += f' (Task running for {time_str})'

        self._console.print(summary)


# Backwards compatibility alias
AsciiProgressMonitor = DottedProgressMonitor
