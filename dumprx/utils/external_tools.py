import os
import subprocess
from pathlib import Path

class ExternalToolsManager:
    def __init__(self, utils_dir, console, verbose=False):
        self.utils_dir = Path(utils_dir).parent / "utils"
        self.console = console
        self.verbose = verbose
        
        self.external_tools = [
            "bkerler/oppo_ozip_decrypt",
            "bkerler/oppo_decrypt", 
            "marin-m/vmlinux-to-elf",
            "ShivamKumarJha/android_tools",
            "HemanthJabalpuri/pacextractor"
        ]
    
    def setup_tools(self):
        self.console.print("[blue]🔧 Setting up external tools...[/blue]")
        
        for tool_slug in self.external_tools:
            tool_name = tool_slug.split('/')[-1]
            tool_dir = self.utils_dir / tool_name
            
            if not tool_dir.exists():
                self._clone_tool(tool_slug, tool_dir)
            else:
                self._update_tool(tool_dir)
    
    def _clone_tool(self, tool_slug, tool_dir):
        try:
            self.console.print(f"[blue]📥 Cloning {tool_slug}...[/blue]")
            result = subprocess.run([
                "git", "clone", "-q", f"https://github.com/{tool_slug}.git", str(tool_dir)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.console.print(f"[green]✅ Cloned {tool_slug}[/green]")
            else:
                if self.verbose:
                    self.console.print(f"[yellow]⚠️  Failed to clone {tool_slug}: {result.stderr}[/yellow]")
        except Exception as e:
            if self.verbose:
                self.console.print(f"[yellow]⚠️  Error cloning {tool_slug}: {str(e)}[/yellow]")
    
    def _update_tool(self, tool_dir):
        try:
            result = subprocess.run([
                "git", "-C", str(tool_dir), "pull"
            ], capture_output=True, text=True)
            
            if self.verbose and result.returncode == 0:
                self.console.print(f"[green]✅ Updated {tool_dir.name}[/green]")
        except Exception as e:
            if self.verbose:
                self.console.print(f"[yellow]⚠️  Error updating {tool_dir.name}: {str(e)}[/yellow]")