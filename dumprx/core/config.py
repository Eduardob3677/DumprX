import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class UIConfig:
    colors: Dict[str, str]
    emojis: Dict[str, str]

@dataclass  
class DownloadConfig:
    timeout: int
    max_retries: int
    chunk_size: int
    aria2c_args: str

@dataclass
class GitConfig:
    commit_batch_size: int
    max_file_size: str
    split_size: str

@dataclass
class TelegramConfig:
    default_chat: str

@dataclass
class AsyncConfig:
    max_workers: int
    download_workers: int
    extract_workers: int

class Config:
    def __init__(self, project_dir: Optional[str] = None):
        if project_dir is None:
            project_dir = Path(__file__).parent.parent.parent.absolute()
        
        self.project_dir = Path(project_dir)
        self.config_file = self.project_dir / "config.yaml"
        
        self.version = "2.0.0"
        self.paths: Dict[str, str] = {}
        self.tools: Dict[str, str] = {}
        self.external_tools: List[str] = []
        self.partitions: List[str] = []
        self.ext4_partitions: List[str] = []
        self.other_partitions: Dict[str, str] = {}
        self.ui: UIConfig = UIConfig({}, {})
        self.downloads: DownloadConfig = DownloadConfig(300, 3, 8192, "")
        self.git: GitConfig = GitConfig(100, "62M", "47M")
        self.telegram: TelegramConfig = TelegramConfig("@DumprXDumps")
        self.async_config: AsyncConfig = AsyncConfig(4, 2, 2)
        
        self.github_token = self._load_token('.github_token')
        self.gitlab_token = self._load_token('.gitlab_token')
        self.telegram_token = self._load_token('.tg_token')
        self.telegram_chat_id = self._load_token('.tg_chat')
        
        self._load_config()
    
    def _load_token(self, filename: str) -> Optional[str]:
        token_file = self.project_dir / filename
        if token_file.exists():
            try:
                return token_file.read_text().strip()
            except Exception:
                pass
        return None
    
    def _load_config(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                if not config_data:
                    return
                
                self.version = config_data.get('version', self.version)
                self.paths = config_data.get('paths', {})
                self.tools = config_data.get('tools', {})
                self.external_tools = config_data.get('external_tools', [])
                self.partitions = config_data.get('partitions', [])
                self.ext4_partitions = config_data.get('ext4_partitions', [])
                self.other_partitions = config_data.get('other_partitions', {})
                
                ui_config = config_data.get('ui', {})
                self.ui = UIConfig(
                    colors=ui_config.get('colors', {}),
                    emojis=ui_config.get('emojis', {})
                )
                
                download_config = config_data.get('downloads', {})
                self.downloads = DownloadConfig(
                    timeout=download_config.get('timeout', 300),
                    max_retries=download_config.get('max_retries', 3),
                    chunk_size=download_config.get('chunk_size', 8192),
                    aria2c_args=download_config.get('aria2c_args', "")
                )
                
                git_config = config_data.get('git', {})
                self.git = GitConfig(
                    commit_batch_size=git_config.get('commit_batch_size', 100),
                    max_file_size=git_config.get('max_file_size', "62M"),
                    split_size=git_config.get('split_size', "47M")
                )
                
                telegram_config = config_data.get('telegram', {})
                self.telegram = TelegramConfig(
                    default_chat=telegram_config.get('default_chat', "@DumprXDumps")
                )
                
                async_config = config_data.get('async', {})
                self.async_config = AsyncConfig(
                    max_workers=async_config.get('max_workers', 4),
                    download_workers=async_config.get('download_workers', 2),
                    extract_workers=async_config.get('extract_workers', 2)
                )
                
            except Exception as e:
                print(f"Error loading config: {e}")
    
    def get_path(self, key: str) -> str:
        base_path = self.paths.get(key, "")
        if base_path.startswith("./"):
            return str(self.project_dir / base_path[2:])
        return base_path
    
    def get_tool_path(self, tool: str) -> str:
        tool_path = self.tools.get(tool, "")
        if tool_path.startswith("./"):
            return str(self.project_dir / tool_path[2:])
        return tool_path
    
    def create_directories(self):
        for key in ['input', 'output', 'temp']:
            path = Path(self.get_path(key))
            path.mkdir(parents=True, exist_ok=True)
    
    def get_download_dir(self) -> str:
        return self.get_path('input')
    
    def get_output_dir(self) -> str:
        return self.get_path('output')
    
    def get_temp_dir(self) -> str:
        return self.get_path('temp')
    
    def get_utils_dir(self) -> str:
        return self.get_path('utils')