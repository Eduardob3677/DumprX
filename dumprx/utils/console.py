from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, TaskID
from typing import Optional

console = Console()

def banner() -> Panel:
    """Generate the DumprX banner"""
    ascii_art = """
	██████╗░██╗░░░██╗███╗░░░███╗██████╗░██████╗░██╗░░██╗
	██╔══██╗██║░░░██║████╗░████║██╔══██╗██╔══██╗╚██╗██╔╝
	██║░░██║██║░░░██║██╔████╔██║██████╔╝██████╔╝░╚███╔╝░
	██║░░██║██║░░░██║██║╚██╔╝██║██╔═══╝░██╔══██╗░██╔██╗░
	██████╔╝╚██████╔╝██║░╚═╝░██║██║░░░░░██║░░██║██╔╝╚██╗
	╚═════╝░░╚═════╝░╚═╝░░░░░╚═╝╚═╝░░░░░╚═╝░░╚═╝╚═╝░░╚═╝
    """
    
    return Panel(
        Text(ascii_art, style="green"),
        title="DumprX v2.0",
        subtitle="Modern Firmware Extraction Tool"
    )

def success(message: str) -> None:
    """Print success message"""
    console.print(f"[green]✓ {message}[/green]")

def error(message: str) -> None:
    """Print error message"""
    console.print(f"[red]✗ {message}[/red]")

def warning(message: str) -> None:
    """Print warning message"""
    console.print(f"[yellow]⚠ {message}[/yellow]")

def info(message: str) -> None:
    """Print info message"""
    console.print(f"[blue]ℹ {message}[/blue]")

def usage() -> None:
    """Print usage information"""
    usage_text = """
[bold green]Usage:[/bold green] dumprx extract <firmware_file_or_url>

[bold blue]Supported Websites:[/bold blue]
• Directly accessible download links from any website
• Filehosters: mega.nz, mediafire, gdrive, onedrive, androidfilehost

[bold blue]Supported File Formats:[/bold blue]
• Archives: *.zip, *.rar, *.7z, *.tar, *.tar.gz, *.tgz, *.tar.md5
• Firmware: *.ozip, *.ofp, *.ops, *.kdz, ruu_*.exe
• Images: system.new.dat*, system.new.img, system.img, UPDATE.APP
• Android: *.emmc.img, *.img.ext4, system.bin, payload.bin
• Other: *.nb0, *chunk*, *.pac, *super*.img, *system*.sin

[bold yellow]Note:[/bold yellow] Wrap URLs in quotes when using from command line
    """
    console.print(Panel(usage_text, title="DumprX Help"))

class ProgressManager:
    def __init__(self):
        self.progress = Progress()
        self.tasks = {}
    
    def __enter__(self):
        self.progress.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.progress.stop()
    
    def add_task(self, description: str, total: Optional[int] = None) -> TaskID:
        task_id = self.progress.add_task(description, total=total)
        self.tasks[description] = task_id
        return task_id
    
    def update_task(self, task_id: TaskID, advance: int = 1, **kwargs):
        self.progress.update(task_id, advance=advance, **kwargs)
    
    def get_task(self, description: str) -> Optional[TaskID]:
        return self.tasks.get(description)