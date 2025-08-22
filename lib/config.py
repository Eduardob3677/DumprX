from typing import Dict, Any, Optional
import yaml
import os
from pathlib import Path

class Config:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> None:
        try:
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f)
        except FileNotFoundError:
            self._config = self._get_default_config()
            self.save()
    
    def save(self) -> None:
        with open(self.config_path, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False)
    
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
    
    def _get_default_config(self) -> Dict[str, Any]:
        return {
            'logging': {
                'level': 'INFO',
                'file': '',
                'max_size': '10MB',
                'backup_count': 5
            },
            'advanced': {
                'max_memory_file_size': 100,
                'max_workers': 4,
                'experimental': False
            },
            'git': {
                'github': {'token': '', 'organization': ''},
                'gitlab': {'token': '', 'group': '', 'instance': 'gitlab.com'}
            },
            'telegram': {
                'token': '',
                'chat_id': '@DumprXDumps',
                'enabled': True
            },
            'download': {
                'user_agents': {
                    'default': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'mega': 'MEGAsync/4.8.8.0'
                },
                'chunk_size': 8192,
                'timeout': 300,
                'retry_attempts': 3,
                'retry_delay': 5
            }
        }

config = Config()