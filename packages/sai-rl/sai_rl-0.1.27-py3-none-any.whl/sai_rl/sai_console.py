import time
from datetime import date

from rich.console import Console, Group
from rich.theme import Theme
from rich.traceback import install
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.status import Status
from rich.align import Align
from typing import Optional, Any, Callable

from sai_rl.utils import config

install(show_locals=True)

LOGO_ART = """[bold white]

      ########      ###     ###########
    #+#    #+#   #+# #+#       #+#
   +#+         +#+   +#+      +#+
  +########+ +#########+     +#+
        +#+ +#+     +#+     +#+
#+#    #+# #+#     #+#     #+#
########  ###     ### ###########
"""

LINKS = f"""[bold white][link={config.platform_url}/dashboard]Platform[/link] • [link=https://docs.competesai.com]Documentation[/link][/bold white]"""

CUSTOM_THEME = Theme(
    {
        "debug": "dim cyan",
        "info": "cyan",
        "success": "bold green",
        "warning": "bold yellow",
        "error": "bold red",
        "error_details": "red",
        "highlight": "bold cyan",
        "muted": "dim",
        "section.title": "bold cyan",
        "section.border": "cyan",
    }
)


class SAIStatus:
    """Wrapper for Rich Status to provide consistent formatting"""

    def __init__(self, status: Status):
        self._status = status

    def update(self, status_text=None, *, spinner=None, spinner_style=None, speed=None):
        """Update status with consistent formatting"""
        return self._status.update(
            f"[highlight]{status_text}\n" if status_text else None,
            spinner=spinner,
            spinner_style=spinner_style,
            speed=speed,
        )

    def stop(self):
        """Stop the status animation"""
        return self._status.stop()

    def start(self):
        """Start the status animation"""
        return self._status.start()

    def __enter__(self):
        self._status.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._status.__exit__(exc_type, exc_val, exc_tb)


class SAIConsole:
    """Centralized console output manager for consistent messaging"""

    def __init__(
        self,
        theme: Optional[Theme] = None,
        is_verbose: bool = False,
        width: Optional[int] = 100,
    ):
        self.console = Console(theme=theme if theme is not None else CUSTOM_THEME)
        self._is_verbose = is_verbose
        self.width = width

    @property
    def is_verbose(self) -> bool:
        return self._is_verbose

    def display_title(self, version: str, editable: bool = False):
        """Display the SAI title screen"""
        panel_group = Group(
            Align.center(Text.from_markup(LOGO_ART)),
            Align.right(
                Text.from_markup(
                    f"[bold white]v{version}{' (editable)' if editable else ''}[/bold white]"
                )
            ),
            Align.right(
                Text.from_markup(f"[dim]© {date.today().year} ArenaX Labs[/dim]")
            ),
        )

        panel = self.panel(
            panel_group,
            padding=(0, 2),
            border_style="white",
        )
        self.console.print(panel)

    def section(self, title: str):
        """Print a section header"""
        self.console.rule(
            f"[section.title]{title}[/section.title]", style="section.border"
        )

    def debug(self, message: str):
        """Display debug message"""
        if self.is_verbose:
            self.console.print(f"[debug]{message}[/debug]")

    def info(self, message: str):
        """Display informational message"""
        self.console.print(f"[info]{message}[/info]")

    def success(self, message: str):
        """Display success message"""
        self.console.print(f"[success]✓ {message}[/success]")

    def warning(self, message: str):
        """Display warning message"""
        self.console.print(f"[warning]⚠ {message}[/warning]")

    def error(self, message: str, exception: Optional[Exception] = None):
        """Display error message with optional exception details"""
        self.console.print(f"[error]✗ {message}[/error]")
        if exception:
            self.console.print(f"[error_details]  {str(exception)}[/error_details]")

    def status(self, message: Optional[str] = None, **kwargs: Any) -> SAIStatus:
        """Create a status with message"""
        status = self.console.status(
            f"[highlight]{message}\n",
            spinner="dots",
            spinner_style="highlight",
            **kwargs,
        )
        return SAIStatus(status)

    def group(self, *args, **kwargs):
        """Create a group of panels"""
        return Group(*args, **kwargs)

    def progress(self, description: str = "Progress") -> Progress:
        """Create an enhanced progress bar"""
        return Progress(
            SpinnerColumn(style="highlight"),
            TextColumn(f"[highlight]{description}"),
            BarColumn(complete_style="highlight"),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=self.console,
        )

    def timed_operation(
        self, message: str, operation: Callable, success_message: Optional[str] = None
    ):
        """Execute an operation with spinner and timing"""
        with self.status(message) as status:
            start_time = time.time()
            result = operation()
            duration = time.time() - start_time

            if success_message:
                status.update(f"[success]{success_message} ({duration:.2f}s)")

            return result

    def panel(
        self,
        content: Any,
        title: Optional[str] = None,
        title_align: str = "left",
        **kwargs: Any,
    ) -> Panel:
        """Create a bordered panel with optional title"""
        border_style = kwargs.pop("border_style", "section.border")

        return Panel(
            content,
            title=title,
            border_style=border_style,
            title_align=title_align,  # type: ignore
            width=self.width,
            **kwargs,
        )

    def text(self, text: str, style: Optional[str] = None) -> Text:
        """Create styled text"""
        return Text(text, style=style or "")

    def table(self, title: Optional[str] = None, **kwargs: Any) -> Table:
        """Create formatted table"""
        table = Table(title=title, **kwargs)
        return table

    def print(self, *args, **kwargs):
        """Print"""
        self.console.print(*args, **kwargs)
