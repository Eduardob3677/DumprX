import os
import yaml
from pathlib import Path


class Config:
    def __init__(self, config_path=None):
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
    
    def _get_default_config_path(self):
        return Path.home() / '.dumprx' / 'config.yml'
    
    def _load_config(self):
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def _save_config(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value
        self._save_config()
    
    def show_all(self):
        from utils.console import Console
        console = Console()
        
        if not self.config:
            console.info("No configuration found")
            return
        
        console.info("Current configuration:")
        for key, value in self.config.items():
            console.info(f"  {key}: {value}")
    
    @property
    def github_token(self):
        token = self.get('github_token')
        if not token:
            token_file = Path('.github_token')
            if token_file.exists():
                with open(token_file, 'r') as f:
                    token = f.read().strip()
                    self.set('github_token', token)
        return token
    
    @property
    def gitlab_token(self):
        token = self.get('gitlab_token')
        if not token:
            token_file = Path('.gitlab_token')
            if token_file.exists():
                with open(token_file, 'r') as f:
                    token = f.read().strip()
                    self.set('gitlab_token', token)
        return token
    
    @property
    def telegram_token(self):
        token = self.get('telegram_token')
        if not token:
            token_file = Path('.tg_token')
            if token_file.exists():
                with open(token_file, 'r') as f:
                    token = f.read().strip()
                    self.set('telegram_token', token)
        return token
    
    @property
    def telegram_chat(self):
        chat = self.get('telegram_chat')
        if not chat:
            chat_file = Path('.tg_chat')
            if chat_file.exists():
                with open(chat_file, 'r') as f:
                    chat = f.read().strip()
                    self.set('telegram_chat', chat)
        return chat or "@DumprXDumps"
    
    @property
    def git_org(self):
        return self.get('git_org', self.get('git_user', ''))
    
    @property
    def git_user(self):
        return self.get('git_user', '')