"""
Console utilities using Rich for beautiful output.

Provides consistent console output with colors, progress bars, and formatting.
"""

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from typing import Optional, Any

from ..modules.banner import create_banner, create_usage_banner, create_error_banner, create_success_banner

# Global console instance
console = Console()


def print_banner():
    """Print the main DumprX banner."""
    console.print(create_banner())


def print_usage():
    """Print usage information."""
    console.print(create_usage_banner())


def print_error(message: str, title: str = "Error"):
    """
    Print error message with red styling.
    
    Args:
        message: Error message to display
        title: Title for the error panel
    """
    console.print(f"[bold red]❌ {title}:[/bold red] {message}")


def print_success(message: str, title: str = "Success"):
    """
    Print success message with green styling.
    
    Args:
        message: Success message to display
        title: Title for the success panel
    """
    console.print(f"[bold green]✅ {title}:[/bold green] {message}")


def print_info(message: str, title: str = "Info"):
    """
    Print info message with blue styling.
    
    Args:
        message: Info message to display
        title: Title for the info panel
    """
    console.print(f"[bold cyan]ℹ️  {title}:[/bold cyan] {message}")


def print_warning(message: str, title: str = "Warning"):
    """
    Print warning message with yellow styling.
    
    Args:
        message: Warning message to display
        title: Title for the warning panel
    """
    console.print(f"[bold yellow]⚠️  {title}:[/bold yellow] {message}")


def print_step(step: str, description: str = ""):
    """
    Print a processing step with styling.
    
    Args:
        step: Step name
        description: Optional step description
    """
    text = f"[bold cyan]→[/bold cyan] {step}"
    if description:
        text += f": {description}"
    console.print(text)


def print_substep(substep: str, description: str = ""):
    """
    Print a processing substep with styling.
    
    Args:
        substep: Substep name
        description: Optional substep description
    """
    text = f"  [cyan]•[/cyan] {substep}"
    if description:
        text += f": {description}"
    console.print(text)


def create_progress_bar(description: str = "Processing...") -> Progress:
    """
    Create a Rich progress bar.
    
    Args:
        description: Description for the progress bar
        
    Returns:
        Configured Progress instance
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    )


def prompt_user(message: str, default: Optional[str] = None) -> str:
    """
    Prompt user for input.
    
    Args:
        message: Prompt message
        default: Default value if user presses enter
        
    Returns:
        User input
    """
    return Prompt.ask(message, default=default)


def confirm_user(message: str, default: bool = False) -> bool:
    """
    Prompt user for confirmation.
    
    Args:
        message: Confirmation message
        default: Default value if user presses enter
        
    Returns:
        User confirmation
    """
    return Confirm.ask(message, default=default)


def print_panel(content: str, title: str = "", border_style: str = "blue"):
    """
    Print content in a panel.
    
    Args:
        content: Content to display in panel
        title: Panel title
        border_style: Border style/color
    """
    panel = Panel(content, title=title, border_style=border_style)
    console.print(panel)


def print_table_header(headers: list, widths: list):
    """
    Print table header.
    
    Args:
        headers: List of header names
        widths: List of column widths
    """
    from ..modules.formatter import format_table_row
    
    header_row = format_table_row(headers, widths)
    separator = "─" * len(header_row)
    
    console.print(f"[bold cyan]{header_row}[/bold cyan]")
    console.print(f"[cyan]{separator}[/cyan]")


def print_table_row(columns: list, widths: list):
    """
    Print table row.
    
    Args:
        columns: List of column values
        widths: List of column widths
    """
    from ..modules.formatter import format_table_row
    
    row = format_table_row(columns, widths)
    console.print(row)


def clear_console():
    """Clear the console."""
    console.clear()


def print_json(data: Any, title: str = "JSON Data"):
    """
    Print JSON data with syntax highlighting.
    
    Args:
        data: Data to print as JSON
        title: Title for the panel
    """
    import json
    from rich.syntax import Syntax
    
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
    
    panel = Panel(syntax, title=title, border_style="blue")
    console.print(panel)


def print_code(code: str, language: str = "python", title: str = "Code"):
    """
    Print code with syntax highlighting.
    
    Args:
        code: Code to display
        language: Programming language for syntax highlighting
        title: Title for the panel
    """
    from rich.syntax import Syntax
    
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    panel = Panel(syntax, title=title, border_style="blue")
    console.print(panel)


class ProgressContext:
    """Context manager for progress operations."""
    
    def __init__(self, description: str = "Processing..."):
        self.description = description
        self.progress = None
        self.task = None
    
    def __enter__(self):
        self.progress = create_progress_bar(self.description)
        self.task = self.progress.add_task(self.description, total=100)
        self.progress.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.progress:
            self.progress.stop()
    
    def update(self, completed: int, total: int = 100):
        """Update progress."""
        if self.progress and self.task:
            percentage = (completed / total) * 100 if total > 0 else 100
            self.progress.update(self.task, completed=percentage)
    
    def set_description(self, description: str):
        """Update progress description."""
        if self.progress and self.task:
            self.progress.update(self.task, description=description)


def with_spinner(func):
    """Decorator to show spinner during function execution."""
    def wrapper(*args, **kwargs):
        with console.status("[bold green]Working...") as status:
            return func(*args, **kwargs)
    return wrapper