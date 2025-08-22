import sys
from rich.console import Console as RichConsole
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text


class Console:
    def __init__(self):
        self.rich_console = RichConsole()
    
    def info(self, message: str):
        self.rich_console.print(f"[blue]ℹ[/blue] {message}")
    
    def success(self, message: str):
        self.rich_console.print(f"[green]✓[/green] {message}")
    
    def warning(self, message: str):
        self.rich_console.print(f"[yellow]⚠[/yellow] {message}")
    
    def error(self, message: str):
        self.rich_console.print(f"[red]✗[/red] {message}", file=sys.stderr)
    
    def print(self, message: str, style: str = None):
        if style:
            self.rich_console.print(message, style=style)
        else:
            self.rich_console.print(message)
    
    def panel(self, message: str, title: str = None, style: str = "blue"):
        panel = Panel(message, title=title, border_style=style)
        self.rich_console.print(panel)
    
    def progress(self):
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.rich_console
        )