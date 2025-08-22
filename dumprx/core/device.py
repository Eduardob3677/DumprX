import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Optional

class DeviceInfo:
    def __init__(self, firmware_path: str):
        self.firmware_path = firmware_path
        self.device_data = {}
        
    def extract_device_info(self) -> Dict[str, str]:
        """Extract device information from firmware"""
        self.device_data = {
            'brand': self._extract_brand(),
            'codename': self._extract_codename(),
            'model': self._extract_model(),
            'platform': self._extract_platform(),
            'manufacturer': self._extract_manufacturer(),
            'fingerprint': self._extract_fingerprint(),
            'description': self._extract_description(),
            'android_version': self._extract_android_version(),
            'security_patch': self._extract_security_patch(),
            'build_id': self._extract_build_id(),
            'kernel_version': self._extract_kernel_version()
        }
        
        return self.device_data
    
    def _extract_brand(self) -> str:
        """Extract brand from firmware"""
        return self._get_prop_value('ro.product.brand', 'Unknown')
    
    def _extract_codename(self) -> str:
        """Extract device codename"""
        return self._get_prop_value('ro.product.device', 'unknown')
    
    def _extract_model(self) -> str:
        """Extract device model"""
        return self._get_prop_value('ro.product.model', 'Unknown')
    
    def _extract_platform(self) -> str:
        """Extract platform information"""
        return self._get_prop_value('ro.board.platform', 'unknown')
    
    def _extract_manufacturer(self) -> str:
        """Extract manufacturer"""
        return self._get_prop_value('ro.product.manufacturer', 'Unknown')
    
    def _extract_fingerprint(self) -> str:
        """Extract build fingerprint"""
        return self._get_prop_value('ro.build.fingerprint', '')
    
    def _extract_description(self) -> str:
        """Extract build description"""
        return self._get_prop_value('ro.build.description', '')
    
    def _extract_android_version(self) -> str:
        """Extract Android version"""
        return self._get_prop_value('ro.build.version.release', 'Unknown')
    
    def _extract_security_patch(self) -> str:
        """Extract security patch level"""
        return self._get_prop_value('ro.build.version.security_patch', 'Unknown')
    
    def _extract_build_id(self) -> str:
        """Extract build ID"""
        return self._get_prop_value('ro.build.id', 'Unknown')
    
    def _extract_kernel_version(self) -> str:
        """Extract kernel version from boot image"""
        kernel_version = "Unknown"
        
        boot_config = Path("bootRE/ikconfig")
        if boot_config.exists():
            try:
                with open(boot_config, 'r') as f:
                    content = f.read()
                    match = re.search(r'Kernel Configuration.*?(\d+\.\d+\.\d+)', content)
                    if match:
                        kernel_version = match.group(1)
            except Exception:
                pass
        
        return kernel_version
    
    def _get_prop_value(self, prop_name: str, default: str = "") -> str:
        """Extract property value from build.prop files"""
        prop_files = [
            "system/build.prop",
            "system/system/build.prop", 
            "vendor/build.prop",
            "odm/build.prop",
            "product/build.prop"
        ]
        
        for prop_file in prop_files:
            if os.path.exists(prop_file):
                try:
                    with open(prop_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        pattern = f'^{re.escape(prop_name)}=(.*)$'
                        match = re.search(pattern, content, re.MULTILINE)
                        if match:
                            return match.group(1).strip()
                except Exception:
                    continue
        
        return default
    
    def generate_repo_name(self) -> str:
        """Generate repository name based on device info"""
        brand = self.device_data.get('brand', 'unknown').lower()
        codename = self.device_data.get('codename', 'unknown').lower()
        
        brand = re.sub(r'[^a-z0-9]', '', brand)
        codename = re.sub(r'[^a-z0-9]', '', codename)
        
        return f"{brand}_{codename}_dump"
    
    def generate_branch_name(self) -> str:
        """Generate branch name from description"""
        description = self.device_data.get('description', '')
        if description:
            branch = re.sub(r'[^a-zA-Z0-9]', '-', description)
            branch = re.sub(r'-+', '-', branch)
            return branch.strip('-').lower()
        
        android_version = self.device_data.get('android_version', 'unknown')
        return f"android-{android_version}"
    
    def sanitize_name(self, name: str, max_length: int = 35) -> str:
        """Sanitize name for Git usage"""
        sanitized = re.sub(r'[^a-zA-Z0-9-_]', '-', name)
        sanitized = re.sub(r'-+', '-', sanitized)
        sanitized = sanitized.strip('-').lower()
        return sanitized[:max_length]