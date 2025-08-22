import os
import subprocess
from pathlib import Path
from rich.console import Console

console = Console()

class GitManager:
    def __init__(self, config):
        self.config = config
        
    def setup_git_user(self):
        user_name = self.config.get('git.user_name') or 'DumprX User'
        user_email = self.config.get('git.user_email') or 'dumprx@example.com'
        
        try:
            current_name = subprocess.check_output(['git', 'config', '--get', 'user.name'], text=True).strip()
        except:
            current_name = ''
        
        try:
            current_email = subprocess.check_output(['git', 'config', '--get', 'user.email'], text=True).strip()
        except:
            current_email = ''
        
        if not current_name:
            subprocess.run(['git', 'config', 'user.name', user_name], check=True)
        
        if not current_email:
            subprocess.run(['git', 'config', 'user.email', user_email], check=True)
    
    def create_and_push_repo(self, output_dir):
        if not self.config.get('git.auto_push', False):
            console.print("[yellow]Git auto-push disabled[/yellow]")
            return
        
        output_path = Path(output_dir)
        os.chdir(output_path)
        
        self.setup_git_user()
        
        if not (output_path / '.git').exists():
            subprocess.run(['git', 'init'], check=True)
        
        git_org = self.config.get('git.organization') or self.config.get('git.user_name', 'dumprx-user')
        
        device_info = self._get_device_info(output_path)
        repo_name = f"{device_info['brand']}_{device_info['codename']}_{device_info['platform']}"
        branch_name = f"{device_info['codename']}-{device_info['release']}"
        
        remote_url = f"https://github.com/{git_org}/{repo_name}.git"
        
        try:
            existing_remote = subprocess.check_output(['git', 'remote', 'get-url', 'origin'], text=True).strip()
        except:
            subprocess.run(['git', 'remote', 'add', 'origin', remote_url], check=False)
        
        self._commit_and_push(branch_name, device_info['description'])
    
    def _get_device_info(self, output_dir):
        brand = self.config.get('device.brand', 'Unknown')
        codename = self.config.get('device.codename', 'unknown')
        platform = self.config.get('device.platform', 'unknown')
        release = self.config.get('device.release', 'unknown')
        
        description = f"{brand} {codename} {platform} Android {release}"
        
        return {
            'brand': brand,
            'codename': codename,
            'platform': platform,
            'release': release,
            'description': description
        }
    
    def _commit_and_push(self, branch, description):
        dirs_to_commit = [
            'system', 'vendor', 'product', 'odm', 'boot', 'recovery',
            'system_ext', 'system_other', 'vendor_boot'
        ]
        
        subprocess.run(['git', 'checkout', '-b', branch], check=False)
        
        apk_files = list(Path('.').rglob('*.apk'))
        if apk_files:
            for apk in apk_files:
                subprocess.run(['git', 'add', str(apk)], check=False)
            subprocess.run(['git', 'commit', '-sm', f'Add apps for {description}'], check=False)
            self._try_push(branch)
        
        for dir_name in dirs_to_commit:
            if Path(dir_name).exists():
                subprocess.run(['git', 'add', dir_name], check=False)
                subprocess.run(['git', 'commit', '-sm', f'Add {dir_name} for {description}'], check=False)
                self._try_push(branch)
            
            system_dir = Path('system') / dir_name
            if system_dir.exists():
                subprocess.run(['git', 'add', str(system_dir)], check=False)
                subprocess.run(['git', 'commit', '-sm', f'Add {dir_name} for {description}'], check=False)
                self._try_push(branch)
        
        subprocess.run(['git', 'add', '.'], check=False)
        subprocess.run(['git', 'commit', '-sm', f'Add extras for {description}'], check=False)
        self._try_push(branch)
    
    def _try_push(self, branch):
        try:
            subprocess.run(['git', 'push', '-u', 'origin', branch], check=False, timeout=30)
        except subprocess.TimeoutExpired:
            console.print("[yellow]Git push timed out, continuing...[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Git push failed: {e}[/yellow]")