"""
Configuration management for DumprX.

Handles YAML configuration files with legacy token file compatibility.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field


@dataclass
class GitConfig:
    """Git-related configuration."""
    github_token: Optional[str] = None
    github_org: Optional[str] = None
    gitlab_token: Optional[str] = None
    gitlab_group: Optional[str] = None
    gitlab_instance: Optional[str] = None
    push_to_gitlab: bool = False


@dataclass
class TelegramConfig:
    """Telegram notification configuration."""
    token: Optional[str] = None
    chat_id: Optional[str] = None
    enabled: bool = False


@dataclass
class DownloadConfig:
    """Download-related configuration."""
    timeout: int = 300
    retry_count: int = 3
    chunk_size: int = 8192
    user_agent: str = "DumprX/2.0.0"


@dataclass
class ExtractionConfig:
    """Extraction-related configuration."""
    preserve_permissions: bool = True
    create_structure_info: bool = True
    extract_recovery: bool = True
    extract_dtbo: bool = True


@dataclass
class Config:
    """Main configuration class for DumprX."""
    
    project_dir: Path = field(default_factory=lambda: Path.cwd())
    input_dir: Path = field(default_factory=lambda: Path.cwd() / "input")
    output_dir: Path = field(default_factory=lambda: Path.cwd() / "out")
    utils_dir: Path = field(default_factory=lambda: Path.cwd() / "utils")
    bin_dir: Path = field(default_factory=lambda: Path.cwd() / "bin")
    
    git: GitConfig = field(default_factory=GitConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    download: DownloadConfig = field(default_factory=DownloadConfig)
    extraction: ExtractionConfig = field(default_factory=ExtractionConfig)
    
    _config_file: Optional[Path] = None
    
    @classmethod
    def load(cls, config_path: Optional[Union[str, Path]] = None) -> "Config":
        """
        Load configuration from YAML file or legacy token files.
        
        Args:
            config_path: Path to configuration file. If None, searches for default locations.
            
        Returns:
            Loaded configuration instance.
        """
        config = cls()
        
        # Set project directory and derive other paths
        project_dir = Path.cwd()
        config.project_dir = project_dir
        config.input_dir = project_dir / "input"
        config.output_dir = project_dir / "out"
        config.utils_dir = project_dir / "utils"
        config.bin_dir = project_dir / "bin"
        
        # Try to find and load YAML config
        if config_path:
            config_file = Path(config_path)
        else:
            # Search for default config locations
            possible_configs = [
                project_dir / "dumprx.yaml",
                project_dir / "dumprx.yml", 
                project_dir / ".dumprx.yaml",
                project_dir / ".dumprx.yml",
            ]
            config_file = None
            for p in possible_configs:
                if p.exists():
                    config_file = p
                    break
        
        if config_file and config_file.exists():
            config._load_yaml_config(config_file)
            config._config_file = config_file
        
        # Load legacy token files for compatibility
        config._load_legacy_tokens()
        
        return config
    
    def _load_yaml_config(self, config_file: Path) -> None:
        """Load configuration from YAML file."""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            
            # Load git configuration
            if 'git' in data:
                git_data = data['git']
                self.git.github_token = git_data.get('github_token')
                self.git.github_org = git_data.get('github_org')
                self.git.gitlab_token = git_data.get('gitlab_token')
                self.git.gitlab_group = git_data.get('gitlab_group')
                self.git.gitlab_instance = git_data.get('gitlab_instance')
                self.git.push_to_gitlab = git_data.get('push_to_gitlab', False)
            
            # Load telegram configuration
            if 'telegram' in data:
                tg_data = data['telegram']
                self.telegram.token = tg_data.get('token')
                self.telegram.chat_id = tg_data.get('chat_id')
                self.telegram.enabled = tg_data.get('enabled', False)
            
            # Load download configuration
            if 'download' in data:
                dl_data = data['download']
                self.download.timeout = dl_data.get('timeout', 300)
                self.download.retry_count = dl_data.get('retry_count', 3)
                self.download.chunk_size = dl_data.get('chunk_size', 8192)
                self.download.user_agent = dl_data.get('user_agent', "DumprX/2.0.0")
            
            # Load extraction configuration
            if 'extraction' in data:
                ext_data = data['extraction']
                self.extraction.preserve_permissions = ext_data.get('preserve_permissions', True)
                self.extraction.create_structure_info = ext_data.get('create_structure_info', True)
                self.extraction.extract_recovery = ext_data.get('extract_recovery', True)
                self.extraction.extract_dtbo = ext_data.get('extract_dtbo', True)
                
        except Exception as e:
            print(f"Warning: Failed to load YAML config from {config_file}: {e}")
    
    def _load_legacy_tokens(self) -> None:
        """Load legacy token files for backward compatibility."""
        # GitHub tokens
        github_token_file = self.project_dir / ".github_token"
        if github_token_file.exists():
            try:
                self.git.github_token = github_token_file.read_text().strip()
            except Exception:
                pass
        
        github_org_file = self.project_dir / ".github_orgname"
        if github_org_file.exists():
            try:
                self.git.github_org = github_org_file.read_text().strip()
            except Exception:
                pass
        
        # GitLab tokens
        gitlab_token_file = self.project_dir / ".gitlab_token"
        if gitlab_token_file.exists():
            try:
                self.git.gitlab_token = gitlab_token_file.read_text().strip()
            except Exception:
                pass
        
        gitlab_group_file = self.project_dir / ".gitlab_group"
        if gitlab_group_file.exists():
            try:
                self.git.gitlab_group = gitlab_group_file.read_text().strip()
            except Exception:
                pass
        
        gitlab_instance_file = self.project_dir / ".gitlab_instance"
        if gitlab_instance_file.exists():
            try:
                self.git.gitlab_instance = gitlab_instance_file.read_text().strip()
            except Exception:
                pass
        
        # Telegram tokens
        tg_token_file = self.project_dir / ".tg_token"
        if tg_token_file.exists():
            try:
                self.telegram.token = tg_token_file.read_text().strip()
                self.telegram.enabled = True
            except Exception:
                pass
        
        tg_chat_file = self.project_dir / ".tg_chat"
        if tg_chat_file.exists():
            try:
                self.telegram.chat_id = tg_chat_file.read_text().strip()
            except Exception:
                pass
    
    def save(self, config_path: Optional[Union[str, Path]] = None) -> None:
        """
        Save configuration to YAML file.
        
        Args:
            config_path: Path to save configuration. If None, uses default location.
        """
        if config_path:
            config_file = Path(config_path)
        elif self._config_file:
            config_file = self._config_file
        else:
            config_file = self.project_dir / "dumprx.yaml"
        
        config_data = {
            'git': {
                'github_token': self.git.github_token,
                'github_org': self.git.github_org,
                'gitlab_token': self.git.gitlab_token,
                'gitlab_group': self.git.gitlab_group,
                'gitlab_instance': self.git.gitlab_instance,
                'push_to_gitlab': self.git.push_to_gitlab,
            },
            'telegram': {
                'token': self.telegram.token,
                'chat_id': self.telegram.chat_id,
                'enabled': self.telegram.enabled,
            },
            'download': {
                'timeout': self.download.timeout,
                'retry_count': self.download.retry_count,
                'chunk_size': self.download.chunk_size,
                'user_agent': self.download.user_agent,
            },
            'extraction': {
                'preserve_permissions': self.extraction.preserve_permissions,
                'create_structure_info': self.extraction.create_structure_info,
                'extract_recovery': self.extraction.extract_recovery,
                'extract_dtbo': self.extraction.extract_dtbo,
            },
        }
        
        try:
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            self._config_file = config_file
        except Exception as e:
            raise RuntimeError(f"Failed to save configuration to {config_file}: {e}")
    
    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        for directory in [self.input_dir, self.output_dir, self.utils_dir, self.bin_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'project_dir': str(self.project_dir),
            'input_dir': str(self.input_dir),
            'output_dir': str(self.output_dir),
            'utils_dir': str(self.utils_dir),
            'bin_dir': str(self.bin_dir),
            'git': {
                'github_token': self.git.github_token,
                'github_org': self.git.github_org,
                'gitlab_token': self.git.gitlab_token,
                'gitlab_group': self.git.gitlab_group,
                'gitlab_instance': self.git.gitlab_instance,
                'push_to_gitlab': self.git.push_to_gitlab,
            },
            'telegram': {
                'token': self.telegram.token,
                'chat_id': self.telegram.chat_id,
                'enabled': self.telegram.enabled,
            },
            'download': {
                'timeout': self.download.timeout,
                'retry_count': self.download.retry_count,
                'chunk_size': self.download.chunk_size,
                'user_agent': self.download.user_agent,
            },
            'extraction': {
                'preserve_permissions': self.extraction.preserve_permissions,
                'create_structure_info': self.extraction.create_structure_info,
                'extract_recovery': self.extraction.extract_recovery,
                'extract_dtbo': self.extraction.extract_dtbo,
            },
        }