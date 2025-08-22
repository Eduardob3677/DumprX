import os
import subprocess
import requests
from pathlib import Path

from core.config import Config
from core.device import DeviceInfo
from utils.console import Console


class GitManager:
    def __init__(self, output_dir: Path, config: Config):
        self.output_dir = Path(output_dir)
        self.config = config
        self.console = Console()
    
    def create_repository(self, device_info: DeviceInfo):
        os.chdir(self.output_dir)
        
        repo_name = device_info.get_repo_name()
        description = device_info.get_description()
        
        self.console.info("Initializing Git repository...")
        
        self._init_git_repo(device_info)
        
        if self.config.github_token:
            self._create_github_repo(repo_name, description, device_info)
        elif self.config.gitlab_token:
            self._create_gitlab_repo(repo_name, description, device_info)
    
    def _init_git_repo(self, device_info: DeviceInfo):
        subprocess.run(['git', 'init'], check=True)
        subprocess.run(['git', 'config', '--global', 'http.postBuffer', '524288000'], check=True)
        
        branch = f"{device_info.manufacturer}_{device_info.codename}"
        
        try:
            subprocess.run(['git', 'checkout', '-b', branch], check=True)
        except subprocess.CalledProcessError:
            incremental = f"{branch}_incremental"
            subprocess.run(['git', 'checkout', '-b', incremental], check=True)
            branch = incremental
        
        self._create_gitignore()
        self._create_readme(device_info)
        
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Initial firmware dump'], check=True)
    
    def _create_gitignore(self):
        gitignore_content = []
        
        for pattern in ['*sensetime*', '*.lic']:
            for path in self.output_dir.rglob(pattern):
                rel_path = path.relative_to(self.output_dir)
                gitignore_content.append(str(rel_path))
        
        if gitignore_content:
            with open('.gitignore', 'w') as f:
                f.write('\\n'.join(gitignore_content))
    
    def _create_readme(self, device_info: DeviceInfo):
        readme_content = f"""# {device_info.brand} {device_info.codename} Firmware Dump

## Device Information
- **Brand**: {device_info.brand}
- **Manufacturer**: {device_info.manufacturer}
- **Codename**: {device_info.codename}
- **Platform**: {device_info.platform}
- **Android Version**: {device_info.android_version}
- **Build Fingerprint**: {device_info.fingerprint}
"""
        
        if device_info.kernel_version:
            readme_content += f"- **Kernel Version**: {device_info.kernel_version}\\n"
        
        if device_info.security_patch:
            readme_content += f"- **Security Patch**: {device_info.security_patch}\\n"
        
        readme_content += """
## Extraction Information
This firmware dump was extracted using DumprX toolkit.

## File Structure
The dump contains the following partitions and files extracted from the original firmware.
"""
        
        with open('README.md', 'w') as f:
            f.write(readme_content)
    
    def _create_github_repo(self, repo_name: str, description: str, device_info: DeviceInfo):
        self.console.info("Creating GitHub repository...")
        
        headers = {'Authorization': f'token {self.config.github_token}'}
        
        if self.config.git_org == self.config.git_user:
            url = 'https://api.github.com/user/repos'
        else:
            url = f'https://api.github.com/orgs/{self.config.git_org}/repos'
        
        data = {
            'name': repo_name,
            'description': description
        }
        
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 201:
            self.console.success("GitHub repository created")
            self._push_to_github(repo_name, device_info)
        else:
            self.console.warning(f"GitHub repo creation failed: {response.text}")
    
    def _push_to_github(self, repo_name: str, device_info: DeviceInfo):
        remote_url = f"https://{self.config.github_token}@github.com/{self.config.git_org}/{repo_name}.git"
        
        subprocess.run(['git', 'remote', 'add', 'origin', remote_url], check=True)
        
        branch = f"{device_info.manufacturer}_{device_info.codename}"
        subprocess.run(['git', 'push', '-u', 'origin', branch], check=True)
        
        self._update_github_topics(repo_name, device_info)
    
    def _update_github_topics(self, repo_name: str, device_info: DeviceInfo):
        headers = {
            'Authorization': f'token {self.config.github_token}',
            'Accept': 'application/vnd.github.mercy-preview+json'
        }
        
        topics = [
            device_info.platform,
            device_info.manufacturer,
            device_info.top_codename,
            'firmware',
            'dump'
        ]
        
        url = f'https://api.github.com/repos/{self.config.git_org}/{repo_name}/topics'
        data = {'names': topics}
        
        requests.put(url, json=data, headers=headers)
    
    def _create_gitlab_repo(self, repo_name: str, description: str, device_info: DeviceInfo):
        self.console.info("Creating GitLab repository...")
        pass