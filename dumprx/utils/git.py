import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

try:
    import git
    from git import Repo
    GIT_PYTHON_AVAILABLE = True
except ImportError:
    GIT_PYTHON_AVAILABLE = False

from dumprx.core.config import Config
from dumprx.core.device import DeviceInfo
from dumprx.utils.console import console, info, success, warning, error

class GitManager:
    def __init__(self, config: Config):
        self.config = config
        self.git_enabled = config.get('git.enabled', True)
        
    def create_repository(self, output_dir: str, device_info: DeviceInfo) -> Optional[Dict[str, Any]]:
        """Create and populate Git repository"""
        if not self.git_enabled:
            info("Git integration disabled")
            return None
        
        try:
            device_data = device_info.extract_device_info()
            repo_name = device_info.generate_repo_name()
            branch_name = device_info.generate_branch_name()
            
            # Initialize repository
            repo_info = self._initialize_repo(output_dir, repo_name, branch_name)
            
            # Add and commit files
            self._commit_files(output_dir, device_data, repo_info)
            
            # Push to remote if configured
            if self.config.get('git.auto_push', True):
                self._push_to_remote(output_dir, repo_info, device_data)
            
            success(f"Git repository created: {repo_name}")
            return repo_info
            
        except Exception as e:
            error(f"Failed to create Git repository: {e}")
            return None
    
    def _initialize_repo(self, output_dir: str, repo_name: str, branch_name: str) -> Dict[str, Any]:
        """Initialize Git repository"""
        original_cwd = os.getcwd()
        
        try:
            os.chdir(output_dir)
            
            if GIT_PYTHON_AVAILABLE:
                repo = Repo.init()
                repo.config_writer().set_value("user", "name", "DumprX Bot").release()
                repo.config_writer().set_value("user", "email", "dumprx@noreply.com").release()
            else:
                subprocess.run(['git', 'init'], check=True)
                subprocess.run(['git', 'config', 'user.name', 'DumprX Bot'], check=True)
                subprocess.run(['git', 'config', 'user.email', 'dumprx@noreply.com'], check=True)
            
            return {
                'repository': repo_name,
                'branch': branch_name,
                'url': None
            }
            
        finally:
            os.chdir(original_cwd)
    
    def _commit_files(self, output_dir: str, device_data: Dict[str, str], repo_info: Dict[str, Any]) -> None:
        """Add and commit files to repository"""
        original_cwd = os.getcwd()
        
        try:
            os.chdir(output_dir)
            
            # Create initial commit with README
            self._add_and_commit(['README.md'], f"Add README for {device_data.get('description', 'firmware dump')}")
            
            # Add build.prop files
            build_props = self._find_build_prop_files()
            if build_props:
                self._add_and_commit(build_props, f"Add build props for {device_data.get('description', 'firmware')}")
            
            # Add APK files
            apk_files = self._find_apk_files()
            if apk_files:
                self._add_and_commit(apk_files, f"Add apps for {device_data.get('description', 'firmware')}")
            
            # Add other important files by category
            categories = [
                ('system', 'system files'),
                ('vendor', 'vendor files'),
                ('product', 'product files'),
                ('odm', 'ODM files')
            ]
            
            for category, description in categories:
                if os.path.exists(category):
                    self._add_and_commit([category], f"Add {description} for {device_data.get('description', 'firmware')}")
            
            # Add remaining files
            self._add_and_commit(['.'], f"Add extras for {device_data.get('description', 'firmware')}")
            
        finally:
            os.chdir(original_cwd)
    
    def _add_and_commit(self, files: list, message: str) -> None:
        """Add files and create commit"""
        try:
            if GIT_PYTHON_AVAILABLE:
                repo = Repo('.')
                for file_pattern in files:
                    repo.git.add(file_pattern)
                repo.index.commit(message)
            else:
                for file_pattern in files:
                    subprocess.run(['git', 'add', file_pattern], check=True)
                subprocess.run(['git', 'commit', '-m', message], check=True)
                
        except Exception as e:
            warning(f"Failed to commit {files}: {e}")
    
    def _push_to_remote(self, output_dir: str, repo_info: Dict[str, Any], device_data: Dict[str, str]) -> None:
        """Push repository to remote"""
        provider = self.config.get('git.provider', 'github')
        
        if provider == 'github':
            self._push_to_github(repo_info, device_data)
        elif provider == 'gitlab':
            self._push_to_gitlab(repo_info, device_data)
        else:
            warning(f"Unknown Git provider: {provider}")
    
    def _push_to_github(self, repo_info: Dict[str, Any], device_data: Dict[str, str]) -> None:
        """Push to GitHub"""
        github_token = self.config.get('github.token') or self._get_legacy_github_token()
        
        if not github_token:
            warning("GitHub token not configured")
            return
        
        try:
            org = self.config.get('github.organization', 'AndroidDumps')
            repo_name = repo_info['repository']
            branch = repo_info['branch']
            
            # Create remote repository (would need GitHub API integration)
            remote_url = f"https://{github_token}@github.com/{org}/{repo_name}.git"
            
            if GIT_PYTHON_AVAILABLE:
                repo = Repo('.')
                origin = repo.create_remote('origin', remote_url)
                origin.push(refspec=f'{branch}:{branch}')
            else:
                subprocess.run(['git', 'remote', 'add', 'origin', remote_url], check=True)
                subprocess.run(['git', 'push', '-u', 'origin', branch], check=True)
            
            repo_info['url'] = f"https://github.com/{org}/{repo_name}"
            success(f"Pushed to GitHub: {repo_info['url']}")
            
        except Exception as e:
            error(f"Failed to push to GitHub: {e}")
    
    def _push_to_gitlab(self, repo_info: Dict[str, Any], device_data: Dict[str, str]) -> None:
        """Push to GitLab"""
        gitlab_token = self.config.get('gitlab.token') or self._get_legacy_gitlab_token()
        
        if not gitlab_token:
            warning("GitLab token not configured")
            return
        
        try:
            instance = self.config.get('gitlab.instance', 'gitlab.com')
            group = self.config.get('gitlab.group', 'android-dumps')
            repo_name = repo_info['repository']
            branch = repo_info['branch']
            
            remote_url = f"https://oauth2:{gitlab_token}@{instance}/{group}/{repo_name}.git"
            
            if GIT_PYTHON_AVAILABLE:
                repo = Repo('.')
                origin = repo.create_remote('origin', remote_url)
                origin.push(refspec=f'{branch}:{branch}')
            else:
                subprocess.run(['git', 'remote', 'add', 'origin', remote_url], check=True)
                subprocess.run(['git', 'push', '-u', 'origin', branch], check=True)
            
            repo_info['url'] = f"https://{instance}/{group}/{repo_name}"
            success(f"Pushed to GitLab: {repo_info['url']}")
            
        except Exception as e:
            error(f"Failed to push to GitLab: {e}")
    
    def _find_build_prop_files(self) -> list:
        """Find build.prop files"""
        build_props = []
        patterns = [
            "*/build.prop",
            "*/default.prop", 
            "*/prop.default"
        ]
        
        import glob
        for pattern in patterns:
            build_props.extend(glob.glob(pattern, recursive=True))
        
        return build_props
    
    def _find_apk_files(self) -> list:
        """Find APK files"""
        import glob
        return glob.glob("**/*.apk", recursive=True)
    
    def _get_legacy_github_token(self) -> Optional[str]:
        """Get GitHub token from legacy file"""
        token_file = Path(".github_token")
        if token_file.exists():
            return token_file.read_text().strip()
        return None
    
    def _get_legacy_gitlab_token(self) -> Optional[str]:
        """Get GitLab token from legacy file"""
        token_file = Path(".gitlab_token")
        if token_file.exists():
            return token_file.read_text().strip()
        return None