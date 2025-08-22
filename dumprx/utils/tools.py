import shutil
import subprocess
import os
from pathlib import Path
from typing import List
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class ToolManager:
    def __init__(self, config):
        self.config = config
        
    def setup_external_tools(self):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Setting up external tools...", total=len(self.config.external_tools))
            
            for tool_slug in self.config.external_tools:
                tool_name = tool_slug.split('/')[-1]
                tool_path = self.config.utils_dir / tool_name
                
                if not tool_path.exists():
                    progress.update(task, description=f"Cloning {tool_name}...")
                    subprocess.run([
                        "git", "clone", "-q", 
                        f"https://github.com/{tool_slug}.git", 
                        str(tool_path)
                    ], check=True)
                else:
                    progress.update(task, description=f"Updating {tool_name}...")
                    subprocess.run([
                        "git", "-C", str(tool_path), "pull"
                    ], check=True)
                    
                progress.advance(task)
    
    def check_dependencies(self) -> List[str]:
        missing = []
        
        required_commands = ['7zz', 'git', 'python3', 'pip']
        
        for cmd in required_commands:
            if not shutil.which(cmd):
                missing.append(cmd)
        
        return missing
    
    def run_command(self, cmd: List[str], cwd: Path = None, capture_output: bool = False):
        try:
            if capture_output:
                result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
                return result.stdout
            else:
                subprocess.run(cmd, cwd=cwd, check=True)
                return True
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Command failed: {' '.join(cmd)}[/red]")
            if capture_output and e.stdout:
                console.print(f"[yellow]stdout: {e.stdout}[/yellow]")
            if capture_output and e.stderr:
                console.print(f"[red]stderr: {e.stderr}[/red]")
            return False
    
    def extract_with_7z(self, archive_path: Path, extract_to: Path, patterns: List[str] = None):
        cmd = [self.config.bin_7zz, "x", "-y", str(archive_path)]
        if patterns:
            cmd.extend(patterns)
        cmd.extend(["-o" + str(extract_to)])
        
        return self.run_command(cmd)
    
    def list_archive_contents(self, archive_path: Path) -> str:
        cmd = [self.config.bin_7zz, "l", "-ba", str(archive_path)]
        return self.run_command(cmd, capture_output=True)
    
    def check_uv_available(self) -> bool:
        return shutil.which("uvx") is not None or shutil.which("uv") is not None
    
    def run_uv_script(self, script_path: Path, requirements_file: Path = None, args: List[str] = None):
        if not self.check_uv_available():
            console.print("[red]uv not available, falling back to python3[/red]")
            cmd = ["python3", str(script_path)]
        else:
            cmd = ["uv", "run"]
            if requirements_file and requirements_file.exists():
                cmd.extend(["--with-requirements", str(requirements_file)])
            cmd.append(str(script_path))
        
        if args:
            cmd.extend(args)
        
        return self.run_command(cmd)