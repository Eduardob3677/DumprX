import os
import subprocess
from pathlib import Path
from typing import Dict, Optional
from rich.console import Console

class GitManager:
    def __init__(self, config, console: Console):
        self.config = config
        self.console = console
    
    def upload_firmware(self, device_data: Dict[str, str], output_dir: Path) -> bool:
        github_token = self._get_github_token()
        gitlab_token = self._get_gitlab_token()
        
        if github_token:
            return self._upload_to_github(device_data, output_dir, github_token)
        elif gitlab_token:
            return self._upload_to_gitlab(device_data, output_dir, gitlab_token)
        else:
            self.console.print("[yellow]⚠️  No Git tokens found, skipping upload[/yellow]")
            return False
    
    def _get_github_token(self) -> Optional[str]:
        if self.config.github_token_file.exists():
            return self.config.github_token_file.read_text().strip()
        return os.getenv('GITHUB_TOKEN')
    
    def _get_gitlab_token(self) -> Optional[str]:
        if self.config.gitlab_token_file.exists():
            return self.config.gitlab_token_file.read_text().strip()
        return os.getenv('GITLAB_TOKEN')
    
    def _upload_to_github(self, device_data: Dict[str, str], output_dir: Path, token: str) -> bool:
        try:
            self.console.print("[blue]📤 Uploading to GitHub...[/blue]")
            
            codename = device_data.get('codename', 'unknown')
            brand = device_data.get('brand', 'unknown')
            android_version = device_data.get('release', 'unknown')
            
            repo_name = f"dump_{brand}_{codename}_{android_version}"
            branch_name = f"{brand}-{codename}-{android_version}"
            
            os.chdir(output_dir)
            
            self._setup_git_config()
            
            git_org = self._get_git_org()
            
            existing_check = subprocess.run([
                'curl', '-sf', 
                f'https://raw.githubusercontent.com/{git_org}/{repo_name}/{branch_name}/all_files.txt'
            ], capture_output=True)
            
            if existing_check.returncode == 0:
                self.console.print(f"[yellow]⚠️  Firmware already dumped at: https://github.com/{git_org}/{repo_name}/tree/{branch_name}[/yellow]")
                return True
            
            subprocess.run(['git', 'init'], check=True)
            subprocess.run(['git', 'checkout', '-b', branch_name], check=True)
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run([
                'git', 'commit', '-m', 
                f'{brand} {codename}: Add firmware dump\n\nDevice: {codename}\nBrand: {brand}\nAndroid: {android_version}'
            ], check=True)
            
            subprocess.run([
                'git', 'remote', 'add', 'origin',
                f'https://x-access-token:{token}@github.com/{git_org}/{repo_name}.git'
            ], check=True)
            
            subprocess.run(['git', 'push', '-u', 'origin', branch_name], check=True)
            
            self.console.print(f"[green]✅ Successfully uploaded to: https://github.com/{git_org}/{repo_name}/tree/{branch_name}[/green]")
            
            self._send_telegram_notification(device_data, f"https://github.com/{git_org}/{repo_name}/tree/{branch_name}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.console.print(f"[red]❌ GitHub upload failed: {str(e)}[/red]")
            return False
        except Exception as e:
            self.console.print(f"[red]💥 Unexpected upload error: {str(e)}[/red]")
            return False
    
    def _upload_to_gitlab(self, device_data: Dict[str, str], output_dir: Path, token: str) -> bool:
        try:
            self.console.print("[blue]📤 Uploading to GitLab...[/blue]")
            
            codename = device_data.get('codename', 'unknown')
            brand = device_data.get('brand', 'unknown')
            android_version = device_data.get('release', 'unknown')
            
            repo_name = f"dump_{brand}_{codename}_{android_version}"
            branch_name = f"{brand}-{codename}-{android_version}"
            
            os.chdir(output_dir)
            
            self._setup_git_config()
            
            git_org = self._get_git_org()
            gitlab_host = os.getenv('GITLAB_HOST', 'https://gitlab.com')
            gitlab_instance = gitlab_host.replace('https://', '').replace('http://', '')
            
            subprocess.run(['git', 'init'], check=True)
            subprocess.run(['git', 'checkout', '-b', branch_name], check=True)
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run([
                'git', 'commit', '-m',
                f'{brand} {codename}: Add firmware dump\n\nDevice: {codename}\nBrand: {brand}\nAndroid: {android_version}'
            ], check=True)
            
            subprocess.run([
                'git', 'remote', 'add', 'origin',
                f'git@{gitlab_instance}:{git_org}/{repo_name}.git'
            ], check=True)
            
            subprocess.run(['git', 'push', '-u', 'origin', branch_name], check=True)
            
            self.console.print(f"[green]✅ Successfully uploaded to: {gitlab_host}/{git_org}/{repo_name}/-/tree/{branch_name}[/green]")
            
            self._send_telegram_notification(device_data, f"{gitlab_host}/{git_org}/{repo_name}/-/tree/{branch_name}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            self.console.print(f"[red]❌ GitLab upload failed: {str(e)}[/red]")
            return False
        except Exception as e:
            self.console.print(f"[red]💥 Unexpected upload error: {str(e)}[/red]")
            return False
    
    def _setup_git_config(self):
        try:
            result = subprocess.run(['git', 'config', '--get', 'user.email'], capture_output=True, text=True)
            if not result.stdout.strip():
                subprocess.run(['git', 'config', 'user.email', 'dumprx@example.com'], check=True)
            
            result = subprocess.run(['git', 'config', '--get', 'user.name'], capture_output=True, text=True)
            if not result.stdout.strip():
                subprocess.run(['git', 'config', 'user.name', 'DumprX Bot'], check=True)
        except Exception:
            pass
    
    def _get_git_org(self) -> str:
        github_org_file = self.config.project_dir / ".github_orgname"
        if github_org_file.exists():
            return github_org_file.read_text().strip()
        
        try:
            result = subprocess.run(['git', 'config', '--get', 'user.name'], capture_output=True, text=True)
            if result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
        
        return "DumprX"
    
    def _send_telegram_notification(self, device_data: Dict[str, str], repo_url: str):
        try:
            tg_token = None
            if self.config.tg_token_file.exists():
                tg_token = self.config.tg_token_file.read_text().strip()
            
            if not tg_token:
                return
            
            chat_id = "@DumprXDumps"
            if self.config.tg_chat_file.exists():
                chat_id = self.config.tg_chat_file.read_text().strip()
            
            message = f"""<b>Brand:</b> {device_data.get('brand', 'Unknown')}
<b>Device:</b> {device_data.get('codename', 'Unknown')}
<b>Platform:</b> {device_data.get('platform', 'Unknown')}
<b>Android Version:</b> {device_data.get('release', 'Unknown')}"""

            if 'kernel_version' in device_data:
                message += f"\n<b>Kernel Version:</b> {device_data['kernel_version']}"

            message += f"""\n<b>Fingerprint:</b> {device_data.get('fingerprint', 'Unknown')}
<a href="{repo_url}">Repository Link</a>"""

            subprocess.run([
                'curl', '-s',
                f'https://api.telegram.org/bot{tg_token}/sendmessage',
                '--data', f'text={message}&chat_id={chat_id}&parse_mode=HTML&disable_web_page_preview=True'
            ], check=False)
            
            self.console.print("[green]✅ Telegram notification sent[/green]")
            
        except Exception as e:
            self.console.print(f"[yellow]⚠️  Telegram notification failed: {str(e)}[/yellow]")