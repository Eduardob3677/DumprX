import asyncio
import aiohttp
from pathlib import Path
from typing import Optional, Dict, Any
from .ui import UI
from .config import config

class GitProvider:
    def __init__(self, provider_type: str):
        self.provider_type = provider_type
        self.token = config.get(f'git.{provider_type}.token', '')
        
        if provider_type == 'github':
            self.organization = config.get('git.github.organization', '')
            self.base_url = "https://api.github.com"
        elif provider_type == 'gitlab':
            self.group = config.get('git.gitlab.group', '')
            self.instance = config.get('git.gitlab.instance', 'gitlab.com')
            self.base_url = f"https://{self.instance}/api/v4"
    
    async def create_repository(self, name: str, description: str = "") -> Optional[str]:
        if self.provider_type == 'github':
            return await self._create_github_repo(name, description)
        elif self.provider_type == 'gitlab':
            return await self._create_gitlab_repo(name, description)
        return None
    
    async def _create_github_repo(self, name: str, description: str) -> Optional[str]:
        headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        data = {
            'name': name,
            'description': description,
            'public': True
        }
        
        url = f"{self.base_url}/orgs/{self.organization}/repos" if self.organization else f"{self.base_url}/user/repos"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 201:
                        repo_data = await response.json()
                        return repo_data['clone_url']
                    else:
                        UI.error(f"Failed to create GitHub repository: {response.status}")
                        return None
            except Exception as e:
                UI.error(f"GitHub API error: {e}")
                return None
    
    async def _create_gitlab_repo(self, name: str, description: str) -> Optional[str]:
        headers = {
            'PRIVATE-TOKEN': self.token,
            'Content-Type': 'application/json'
        }
        
        namespace_id = await self._get_gitlab_namespace_id() if self.group else None
        
        data = {
            'name': name,
            'description': description,
            'visibility': 'public'
        }
        
        if namespace_id:
            data['namespace_id'] = namespace_id
        
        url = f"{self.base_url}/projects"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 201:
                        repo_data = await response.json()
                        return repo_data['http_url_to_repo']
                    else:
                        UI.error(f"Failed to create GitLab repository: {response.status}")
                        return None
            except Exception as e:
                UI.error(f"GitLab API error: {e}")
                return None
    
    async def _get_gitlab_namespace_id(self) -> Optional[int]:
        if not self.group:
            return None
        
        headers = {'PRIVATE-TOKEN': self.token}
        url = f"{self.base_url}/groups/{self.group}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        group_data = await response.json()
                        return group_data['id']
                    return None
            except:
                return None

class GitManager:
    def __init__(self, work_dir: Path):
        self.work_dir = work_dir
        self.github_provider = GitProvider('github')
        self.gitlab_provider = GitProvider('gitlab')
    
    async def setup_repository(self, device_info: Dict[str, str]) -> bool:
        brand = device_info.get('brand', 'unknown')
        codename = device_info.get('codename', 'unknown')
        repo_name = f"{brand}_{codename}"
        
        github_token_file = Path('.github_token')
        gitlab_token_file = Path('.gitlab_token')
        
        if github_token_file.exists():
            UI.info("Using GitHub for repository upload")
            return await self._setup_github_repo(repo_name, device_info)
        elif gitlab_token_file.exists():
            UI.info("Using GitLab for repository upload")
            return await self._setup_gitlab_repo(repo_name, device_info)
        else:
            UI.warning("No Git provider configured")
            return False
    
    async def _setup_github_repo(self, repo_name: str, device_info: Dict[str, str]) -> bool:
        description = f"Firmware dump for {device_info.get('brand', '')} {device_info.get('codename', '')}"
        
        repo_url = await self.github_provider.create_repository(repo_name, description)
        if not repo_url:
            return False
        
        return await self._commit_and_push(repo_url, device_info)
    
    async def _setup_gitlab_repo(self, repo_name: str, device_info: Dict[str, str]) -> bool:
        description = f"Firmware dump for {device_info.get('brand', '')} {device_info.get('codename', '')}"
        
        repo_url = await self.gitlab_provider.create_repository(repo_name, description)
        if not repo_url:
            return False
        
        return await self._commit_and_push(repo_url, device_info)
    
    async def _commit_and_push(self, repo_url: str, device_info: Dict[str, str]) -> bool:
        try:
            commands = [
                ["git", "init"],
                ["git", "config", "user.email", "dumprx@github.com"],
                ["git", "config", "user.name", "DumprX"],
                ["git", "add", "."],
                ["git", "commit", "-m", f"Add {device_info.get('brand', '')} {device_info.get('codename', '')} firmware dump"],
                ["git", "branch", "-M", "main"],
                ["git", "remote", "add", "origin", repo_url],
                ["git", "push", "-u", "origin", "main"]
            ]
            
            for cmd in commands:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=str(self.work_dir),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    UI.error(f"Git command failed: {' '.join(cmd)}")
                    return False
            
            UI.success(f"Successfully pushed to repository: {repo_url}")
            return True
            
        except Exception as e:
            UI.error(f"Git operation failed: {e}")
            return False

class TelegramNotifier:
    def __init__(self):
        self.token = config.get('telegram.token', '')
        self.chat_id = config.get('telegram.chat_id', '@DumprXDumps')
        self.enabled = config.get('telegram.enabled', True)
    
    async def send_notification(self, device_info: Dict[str, str], repo_url: str) -> bool:
        if not self.enabled or not self.token:
            return True
        
        token_file = Path('.tg_token')
        chat_file = Path('.tg_chat')
        
        if token_file.exists():
            with open(token_file, 'r') as f:
                self.token = f.read().strip()
        
        if chat_file.exists():
            with open(chat_file, 'r') as f:
                self.chat_id = f.read().strip()
        
        if not self.token:
            UI.warning("Telegram token not configured")
            return True
        
        message = self._format_message(device_info, repo_url)
        
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        
        data = {
            'text': message,
            'chat_id': self.chat_id,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, data=data) as response:
                    if response.status == 200:
                        UI.success("Telegram notification sent")
                        return True
                    else:
                        UI.warning(f"Telegram notification failed: {response.status}")
                        return False
            except Exception as e:
                UI.warning(f"Telegram notification error: {e}")
                return False
    
    def _format_message(self, device_info: Dict[str, str], repo_url: str) -> str:
        brand = device_info.get('brand', 'Unknown')
        codename = device_info.get('codename', 'Unknown')
        platform = device_info.get('platform', 'Unknown')
        android_version = device_info.get('android_version', 'Unknown')
        fingerprint = device_info.get('fingerprint', 'Unknown')
        kernel_version = device_info.get('kernel_version', '')
        
        message = f"<b>Brand:</b> {brand}\n"
        message += f"<b>Device:</b> {codename}\n"
        message += f"<b>Platform:</b> {platform}\n"
        message += f"<b>Android Version:</b> {android_version}\n"
        
        if kernel_version:
            message += f"<b>Kernel Version:</b> {kernel_version}\n"
        
        message += f"<b>Fingerprint:</b> {fingerprint}\n"
        message += f"<a href=\"{repo_url}\">Repository</a>"
        
        return message