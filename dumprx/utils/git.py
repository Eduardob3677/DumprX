"""
Git integration utilities using GitPython.

Provides git repository management, auto-creation, and intelligent commits.
"""

import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass

import git
from git import Repo, InvalidGitRepositoryError
import requests

from dumprxcore.config import Config
from dumprxcore.device_info import DeviceInfo
from dumprxconsole import print_info, print_error, print_success, print_warning


@dataclass
class GitResult:
    """Result of git operation."""
    success: bool
    message: str = ""
    repo_url: Optional[str] = None
    commit_hash: Optional[str] = None
    error: Optional[str] = None


class GitManager:
    """Git repository management and operations."""
    
    def __init__(self, config: Config):
        self.config = config
        self.repo: Optional[Repo] = None
    
    def initialize_repository(self, directory: Union[str, Path], device_info: Optional[DeviceInfo] = None) -> GitResult:
        """
        Initialize git repository in directory.
        
        Args:
            directory: Directory to initialize repository in
            device_info: Device information for repository setup
            
        Returns:
            GitResult with operation status
        """
        try:
            repo_path = Path(directory)
            
            # Check if already a git repository
            try:
                self.repo = Repo(repo_path)
                print_info(f"Using existing git repository: {repo_path}")
                return GitResult(success=True, message="Using existing repository")
            except InvalidGitRepositoryError:
                pass
            
            # Initialize new repository
            self.repo = Repo.init(repo_path)
            
            # Configure git user
            self._configure_git_user()
            
            # Create README if device info is available
            if device_info:
                self._create_readme(device_info, repo_path)
            
            # Create .gitignore
            self._create_gitignore(repo_path)
            
            # Add initial files
            self.repo.index.add(['.gitignore'])
            if (repo_path / 'README.md').exists():
                self.repo.index.add(['README.md'])
            
            # Initial commit
            commit_message = "Initial commit"
            if device_info:
                commit_message = f"Initial commit: {device_info.get_repo_name()}"
            
            commit = self.repo.index.commit(commit_message)
            
            print_success(f"Initialized git repository: {repo_path}")
            return GitResult(
                success=True,
                message="Repository initialized",
                commit_hash=commit.hexsha
            )
            
        except Exception as e:
            error_msg = f"Failed to initialize git repository: {e}"
            print_error(error_msg)
            return GitResult(success=False, error=error_msg)
    
    def commit_firmware_dump(self, device_info: DeviceInfo, files_added: List[str]) -> GitResult:
        """
        Commit firmware dump files with intelligent commit message.
        
        Args:
            device_info: Device information
            files_added: List of files added
            
        Returns:
            GitResult with operation status
        """
        if not self.repo:
            return GitResult(success=False, error="No git repository initialized")
        
        try:
            # Add all firmware files
            if files_added:
                self.repo.index.add(files_added)
            else:
                # Add all files if none specified
                self.repo.git.add('.')
            
            # Generate commit message
            commit_message = self._generate_commit_message(device_info, files_added)
            
            # Commit changes
            commit = self.repo.index.commit(commit_message)
            
            print_success(f"Committed firmware dump: {commit.hexsha[:8]}")
            return GitResult(
                success=True,
                message="Firmware dump committed",
                commit_hash=commit.hexsha
            )
            
        except Exception as e:
            error_msg = f"Failed to commit firmware dump: {e}"
            print_error(error_msg)
            return GitResult(success=False, error=error_msg)
    
    def create_remote_repository(self, repo_name: str, device_info: Optional[DeviceInfo] = None) -> GitResult:
        """
        Create remote repository on GitHub or GitLab.
        
        Args:
            repo_name: Repository name
            device_info: Device information for description
            
        Returns:
            GitResult with operation status and repo URL
        """
        if self.config.git.push_to_gitlab and self.config.git.gitlab_token:
            return self._create_gitlab_repository(repo_name, device_info)
        elif self.config.git.github_token:
            return self._create_github_repository(repo_name, device_info)
        else:
            return GitResult(success=False, error="No git hosting token configured")
    
    def push_to_remote(self, repo_url: str, branch: str = "main") -> GitResult:
        """
        Push repository to remote.
        
        Args:
            repo_url: Remote repository URL
            branch: Branch to push
            
        Returns:
            GitResult with operation status
        """
        if not self.repo:
            return GitResult(success=False, error="No git repository initialized")
        
        try:
            # Add remote if not exists
            try:
                origin = self.repo.remote('origin')
            except:
                origin = self.repo.create_remote('origin', repo_url)
            
            # Push to remote
            origin.push(branch)
            
            print_success(f"Pushed to remote repository: {repo_url}")
            return GitResult(
                success=True,
                message="Pushed to remote",
                repo_url=repo_url
            )
            
        except Exception as e:
            error_msg = f"Failed to push to remote: {e}"
            print_error(error_msg)
            return GitResult(success=False, error=error_msg)
    
    def _configure_git_user(self):
        """Configure git user for commits."""
        try:
            # Try to get existing git config
            try:
                user_name = self.repo.config_reader().get_value("user", "name")
                user_email = self.repo.config_reader().get_value("user", "email")
                return
            except:
                pass
            
            # Set default git user
            with self.repo.config_writer() as git_config:
                git_config.set_value("user", "name", "DumprX Bot")
                git_config.set_value("user", "email", "dumprx@noreply.github.com")
                
        except Exception as e:
            print_warning(f"Could not configure git user: {e}")
    
    def _create_readme(self, device_info: DeviceInfo, repo_path: Path):
        """Create README.md file with device information."""
        readme_content = f"""# {device_info.get_repo_name()}

## Device Information

{device_info}

## Firmware Dump

This repository contains the firmware dump for the above device.

### Structure

- `system/` - System partition files
- `vendor/` - Vendor partition files  
- `product/` - Product partition files (if present)
- `boot.img` - Boot image (if present)
- `recovery.img` - Recovery image (if present)
- `board-info.txt` - Device board information

### Build Properties

"""
        
        # Add build properties information
        device_dict = device_info.to_dict()
        for key, value in device_dict.items():
            if value:
                readme_content += f"- **{key.replace('_', ' ').title()}**: {value}\n"
        
        readme_content += f"""
---

*Generated by DumprX v2.0.0*
"""
        
        readme_path = repo_path / "README.md"
        readme_path.write_text(readme_content, encoding='utf-8')
    
    def _create_gitignore(self, repo_path: Path):
        """Create .gitignore file."""
        gitignore_content = """# DumprX generated .gitignore

# Temporary files
*.tmp
*.temp
.DS_Store
Thumbs.db

# Large binary files that shouldn't be in git
*.img.large
*.bin.large

# Build artifacts
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.env

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
"""
        
        gitignore_path = repo_path / ".gitignore"
        gitignore_path.write_text(gitignore_content, encoding='utf-8')
    
    def _generate_commit_message(self, device_info: DeviceInfo, files_added: List[str]) -> str:
        """Generate intelligent commit message."""
        base_message = device_info.get_commit_message()
        
        # Add file statistics
        if files_added:
            file_count = len(files_added)
            base_message += f" ({file_count} files)"
        
        return base_message
    
    def _create_github_repository(self, repo_name: str, device_info: Optional[DeviceInfo] = None) -> GitResult:
        """Create GitHub repository."""
        try:
            headers = {
                'Authorization': f'token {self.config.git.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            description = "Firmware dump"
            if device_info:
                description = f"Firmware dump for {device_info}"
            
            data = {
                'name': repo_name,
                'description': description,
                'private': False,
                'auto_init': False
            }
            
            # Use organization if configured, otherwise personal account
            if self.config.git.github_org:
                url = f'https://api.github.com/orgs/{self.config.git.github_org}/repos'
            else:
                url = 'https://api.github.com/user/repos'
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 201:
                repo_data = response.json()
                repo_url = repo_data['clone_url']
                print_success(f"Created GitHub repository: {repo_url}")
                return GitResult(success=True, message="GitHub repository created", repo_url=repo_url)
            else:
                error_msg = f"GitHub API error: {response.status_code} - {response.text}"
                return GitResult(success=False, error=error_msg)
                
        except Exception as e:
            error_msg = f"Failed to create GitHub repository: {e}"
            return GitResult(success=False, error=error_msg)
    
    def _create_gitlab_repository(self, repo_name: str, device_info: Optional[DeviceInfo] = None) -> GitResult:
        """Create GitLab repository."""
        try:
            gitlab_instance = self.config.git.gitlab_instance or "https://gitlab.com"
            headers = {
                'Authorization': f'Bearer {self.config.git.gitlab_token}',
                'Content-Type': 'application/json'
            }
            
            description = "Firmware dump"
            if device_info:
                description = f"Firmware dump for {device_info}"
            
            data = {
                'name': repo_name,
                'description': description,
                'visibility': 'public',
                'initialize_with_readme': False
            }
            
            # Use group if configured, otherwise personal namespace
            if self.config.git.gitlab_group:
                data['namespace_id'] = self.config.git.gitlab_group
            
            url = f'{gitlab_instance}/api/v4/projects'
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 201:
                repo_data = response.json()
                repo_url = repo_data['http_url_to_repo']
                print_success(f"Created GitLab repository: {repo_url}")
                return GitResult(success=True, message="GitLab repository created", repo_url=repo_url)
            else:
                error_msg = f"GitLab API error: {response.status_code} - {response.text}"
                return GitResult(success=False, error=error_msg)
                
        except Exception as e:
            error_msg = f"Failed to create GitLab repository: {e}"
            return GitResult(success=False, error=error_msg)