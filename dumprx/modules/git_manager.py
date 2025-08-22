import os
import subprocess
from pathlib import Path

class GitManager:
    def __init__(self, output_dir, github_token=None, console=None, verbose=False):
        self.output_dir = Path(output_dir)
        self.github_token = github_token
        self.console = console
        self.verbose = verbose
        
        self.project_root = Path(__file__).parent.parent.parent
        
    def upload_dump(self, device_info=None):
        if not self.github_token:
            self.console.print("[yellow]⚠️  No GitHub token provided, skipping upload[/yellow]")
            return False
        
        self.console.print("[blue]📤 Preparing Git repository for upload...[/blue]")
        
        try:
            self._setup_git_config()
            self._prepare_repository(device_info)
            self._commit_changes(device_info)
            self._push_changes()
            
            self.console.print("[green]✅ Successfully uploaded firmware dump to GitHub[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]❌ Git upload failed: {str(e)}[/red]")
            if self.verbose:
                self.console.print_exception()
            return False
    
    def _setup_git_config(self):
        github_orgname_file = self.project_root / ".github_orgname"
        
        if github_orgname_file.exists():
            with open(github_orgname_file, 'r') as f:
                org_name = f.read().strip()
        else:
            org_name = "DumprX-User"
        
        subprocess.run([
            "git", "config", "user.name", org_name
        ], cwd=self.output_dir, check=True)
        
        subprocess.run([
            "git", "config", "user.email", f"{org_name}@dumprx.local"
        ], cwd=self.output_dir, check=True)
        
        subprocess.run([
            "git", "config", "http.postBuffer", "524288000"
        ], cwd=self.output_dir, check=True)
    
    def _prepare_repository(self, device_info):
        git_dir = self.output_dir / ".git"
        if not git_dir.exists():
            subprocess.run([
                "git", "init"
            ], cwd=self.output_dir, check=True)
            
            subprocess.run([
                "git", "lfs", "install"
            ], cwd=self.output_dir, check=True)
        
        gitlfs_file = self.output_dir / ".gitattributes"
        if not gitlfs_file.exists():
            lfs_patterns = [
                "*.img filter=lfs diff=lfs merge=lfs -text",
                "*.bin filter=lfs diff=lfs merge=lfs -text",
                "*.dat filter=lfs diff=lfs merge=lfs -text",
                "*.br filter=lfs diff=lfs merge=lfs -text",
                "*.zip filter=lfs diff=lfs merge=lfs -text",
                "*.tar filter=lfs diff=lfs merge=lfs -text"
            ]
            
            with open(gitlfs_file, 'w') as f:
                f.write('\n'.join(lfs_patterns) + '\n')
        
        readme_file = self.output_dir / "README.md"
        if not readme_file.exists():
            self._generate_readme(device_info)
    
    def _generate_readme(self, device_info):
        readme_content = f"""# Firmware Dump

## Device Information
"""
        
        if device_info:
            for key, value in device_info.items():
                readme_content += f"- **{key.replace('_', ' ').title()}**: {value}\n"
        else:
            readme_content += "- Device information not available\n"
        
        readme_content += f"""
## Dump Information
- **Dumped with**: DumprX v2.0.0
- **Extraction Date**: {self._get_current_date()}

## Contents
This repository contains the extracted firmware files and partitions.

## Credits
Dumped using [DumprX](https://github.com/Eduardob3677/DumprX) - Modern Python firmware dumping toolkit.
"""
        
        readme_file = self.output_dir / "README.md"
        with open(readme_file, 'w') as f:
            f.write(readme_content)
    
    def _commit_changes(self, device_info):
        subprocess.run([
            "git", "add", "."
        ], cwd=self.output_dir, check=True)
        
        device_name = "Unknown Device"
        if device_info:
            brand = device_info.get('brand', '')
            model = device_info.get('model', '')
            if brand and model:
                device_name = f"{brand} {model}"
            elif model:
                device_name = model
            elif brand:
                device_name = brand
        
        commit_message = f"Add firmware dump for {device_name}"
        
        subprocess.run([
            "git", "commit", "-m", commit_message
        ], cwd=self.output_dir, check=True)
    
    def _push_changes(self):
        subprocess.run([
            "git", "push", "origin", "main"
        ], cwd=self.output_dir, check=True)
    
    def _get_current_date(self):
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")