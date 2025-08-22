import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

class Config:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config_data = self._load_config()
        
    def _get_default_config_path(self) -> str:
        return os.path.expanduser("~/.dumprx/config.yaml")
    
    def _load_config(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_path):
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        return {
            'output_dir': 'out',
            'input_dir': 'input',
            'temp_dir': 'tmp',
            'git': {
                'enabled': True,
                'provider': 'github',
                'auto_push': True
            },
            'telegram': {
                'enabled': False,
                'token': '',
                'chat_id': ''
            },
            'download': {
                'max_retries': 3,
                'chunk_size': 8192,
                'timeout': 30
            }
        }
    
    def save(self) -> None:
        config_dir = os.path.dirname(self.config_path)
        os.makedirs(config_dir, exist_ok=True)
        
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config_data, f, default_flow_style=False)
    
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self.config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        keys = key.split('.')
        current = self.config_data
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
        self.save()
    
    def show(self) -> None:
        from dumprx.utils.console import console
        import json
        
        config_json = json.dumps(self.config_data, indent=2)
        console.print("[bold]Current Configuration:[/bold]")
        console.print(config_json)
    
    def get_legacy_tokens(self) -> Dict[str, str]:
        """Support for legacy token files"""
        tokens = {}
        
        github_token_file = ".github_token"
        gitlab_token_file = ".gitlab_token"
        
        if os.path.exists(github_token_file):
            with open(github_token_file, 'r') as f:
                tokens['github_token'] = f.read().strip()
        
        if os.path.exists(gitlab_token_file):
            with open(gitlab_token_file, 'r') as f:
                tokens['gitlab_token'] = f.read().strip()
        
        return tokens