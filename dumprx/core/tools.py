import subprocess
from pathlib import Path
from typing import List
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import Config


class ExternalToolsManager:
    def __init__(self, config: Config, console: Console):
        self.config = config
        self.console = console
    
    def setup_external_tools(self) -> bool:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            for tool_slug in self.config.external_tools:
                task = progress.add_task(f"Setting up {tool_slug.split('/')[-1]}...")
                
                tool_name = tool_slug.split("/")[-1]
                tool_path = self.config.utils_dir / tool_name
                
                if not tool_path.exists():
                    self._clone_tool(tool_slug, tool_path)
                else:
                    self._update_tool(tool_path)
                
                progress.update(task, completed=100)
        
        return True
    
    def _clone_tool(self, tool_slug: str, tool_path: Path) -> bool:
        try:
            subprocess.run([
                "git", "clone", "-q", 
                f"https://github.com/{tool_slug}.git", 
                str(tool_path)
            ], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            self.console.print(f"[red]Failed to clone {tool_slug}[/red]")
            return False
    
    def _update_tool(self, tool_path: Path) -> bool:
        try:
            subprocess.run([
                "git", "-C", str(tool_path), "pull"
            ], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            self.console.print(f"[yellow]Failed to update {tool_path.name}[/yellow]")
            return False