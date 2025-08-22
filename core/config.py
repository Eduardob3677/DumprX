import os
import yaml
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()

class Config:
    def __init__(self, config_file=None):
        self.config_file = config_file or os.path.expanduser("~/.dumprx/config.yaml")
        self.config_dir = Path(self.config_file).parent
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.default_config = {
            'project_dir': os.getcwd(),
            'input_dir': 'input',
            'output_dir': 'out',
            'tmp_dir': 'out/tmp',
            'git': {
                'auto_push': False,
                'organization': '',
                'user_name': '',
                'user_email': '',
            },
            'gitlab': {
                'enabled': False,
                'host': '',
                'token': '',
                'instance': '',
            },
            'telegram': {
                'enabled': False,
                'token': '',
                'chat_id': '@DumprXDumps',
            },
            'device': {
                'brand': '',
                'codename': '',
                'platform': '',
                'release': '',
                'fingerprint': '',
                'treble_support': True,
                'is_ab': False,
            },
            'external_tools': [
                'bkerler/oppo_ozip_decrypt',
                'bkerler/oppo_decrypt',
                'marin-m/vmlinux-to-elf',
                'ShivamKumarJha/android_tools',
                'HemanthJabalpuri/pacextractor',
            ],
            'partitions': [
                'system', 'system_ext', 'system_other', 'systemex', 'vendor',
                'cust', 'odm', 'oem', 'factory', 'product', 'xrom', 'modem',
                'dtbo', 'dtb', 'boot', 'vendor_boot', 'recovery', 'tz',
                'oppo_product', 'preload_common', 'opproduct', 'reserve',
                'india', 'my_preload', 'my_odm', 'my_stock', 'my_operator',
                'my_country', 'my_product', 'my_company', 'my_engineering',
                'my_heytap', 'my_custom', 'my_manifest', 'my_carrier',
                'my_region', 'my_bigball', 'my_version', 'special_preload',
                'system_dlkm', 'vendor_dlkm', 'odm_dlkm', 'init_boot',
                'vendor_kernel_boot', 'odmko', 'socko', 'nt_log', 'mi_ext',
                'hw_product', 'product_h', 'preas', 'preavs'
            ],
            'ext4_partitions': [
                'system', 'vendor', 'cust', 'odm', 'oem', 'factory',
                'product', 'xrom', 'systemex', 'oppo_product',
                'preload_common', 'hw_product', 'product_h', 'preas', 'preavs'
            ]
        }
        
        self._config = self.load()
    
    def load(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = yaml.safe_load(f) or {}
                
                config = self.default_config.copy()
                self._deep_update(config, loaded_config)
                return config
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load config file: {e}[/yellow]")
                return self.default_config.copy()
        else:
            config = self.default_config.copy()
            self._config = config
            self.save()
            return config
    
    def save(self):
        with open(self.config_file, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False, indent=2)
    
    def _deep_update(self, base_dict, update_dict):
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def get(self, key, default=None):
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key, value):
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save()
    
    def show(self):
        table = Table(title="DumprX Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="magenta")
        
        def add_config_rows(config_dict, prefix=""):
            for key, value in config_dict.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    add_config_rows(value, full_key)
                elif isinstance(value, list):
                    table.add_row(full_key, str(len(value)) + " items")
                else:
                    table.add_row(full_key, str(value))
        
        add_config_rows(self._config)
        console.print(table)
    
    @property
    def project_dir(self):
        return self.get('project_dir', os.getcwd())
    
    @property
    def input_dir(self):
        return os.path.join(self.project_dir, self.get('input_dir', 'input'))
    
    @property
    def output_dir(self):
        return os.path.join(self.project_dir, self.get('output_dir', 'out'))
    
    @property
    def tmp_dir(self):
        return os.path.join(self.project_dir, self.get('tmp_dir', 'out/tmp'))
    
    def get_external_tools(self):
        return self.get('external_tools', [])
    
    def get_partitions(self):
        return self.get('partitions', [])
    
    def get_ext4_partitions(self):
        return self.get('ext4_partitions', [])