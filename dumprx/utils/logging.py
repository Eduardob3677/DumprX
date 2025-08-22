import sys
from typing import Optional
from rich.console import Console
from rich.progress import Progress, TaskID

console = Console()

class Logger:
    def __init__(self):
        self.progress: Optional[Progress] = None
        
    def info(self, message: str):
        console.print(f"[blue]ℹ[/blue] {message}")
        
    def success(self, message: str):
        console.print(f"[green]✓[/green] {message}")
        
    def warning(self, message: str):
        console.print(f"[yellow]⚠[/yellow] {message}")
        
    def error(self, message: str):
        console.print(f"[red]✗[/red] {message}")
        
    def abort(self, message: str):
        self.error(message)
        sys.exit(1)
        
    def create_progress(self) -> Progress:
        self.progress = Progress()
        return self.progress
        
    def start_task(self, description: str, total: int = 100) -> TaskID:
        if not self.progress:
            self.progress = self.create_progress()
        return self.progress.add_task(description, total=total)
        
    def update_task(self, task_id: TaskID, advance: int = 1):
        if self.progress:
            self.progress.update(task_id, advance=advance)

logger = Logger()