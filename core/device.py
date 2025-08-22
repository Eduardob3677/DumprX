import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List


class DeviceInfo:
    def __init__(self, extracted_path: Path):
        self.extracted_path = Path(extracted_path)
        self._info = {}
        self._extract_device_info()
    
    def _extract_device_info(self):
        self._extract_build_prop()
        self._extract_kernel_info()
    
    def _extract_build_prop(self):
        build_prop_paths = [
            self.extracted_path / "system" / "build.prop",
            self.extracted_path / "build.prop",
            self.extracted_path / "system" / "system" / "build.prop"
        ]
        
        for build_prop in build_prop_paths:
            if build_prop.exists():
                self._parse_build_prop(build_prop)
                break
    
    def _parse_build_prop(self, build_prop_path: Path):
        try:
            with open(build_prop_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        self._info[key] = value
        except Exception:
            pass
    
    def _extract_kernel_info(self):
        ikconfig_path = self.extracted_path / "bootRE" / "ikconfig"
        if ikconfig_path.exists():
            try:
                with open(ikconfig_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    for line in content.split('\\n'):
                        if "Kernel Configuration" in line:
                            parts = line.split()
                            if len(parts) >= 3:
                                self._info['kernel_version'] = parts[2]
                                break
            except Exception:
                pass
    
    @property
    def brand(self) -> str:
        return self._info.get('ro.product.brand', 'Unknown')
    
    @property
    def manufacturer(self) -> str:
        return self._info.get('ro.product.manufacturer', self.brand)
    
    @property
    def codename(self) -> str:
        codename = self._info.get('ro.product.device')
        if not codename:
            codename = self._info.get('ro.build.product', 'Unknown')
        return codename
    
    @property
    def top_codename(self) -> str:
        codename = self.codename
        if '_' in codename:
            return codename.split('_')[0]
        return codename
    
    @property
    def platform(self) -> str:
        platform = self._info.get('ro.board.platform')
        if not platform:
            platform = self._info.get('ro.hardware.chipset')
            if not platform:
                platform = self._info.get('ro.hardware', 'Unknown')
        return platform
    
    @property
    def android_version(self) -> str:
        return self._info.get('ro.build.version.release', 'Unknown')
    
    @property
    def fingerprint(self) -> str:
        return self._info.get('ro.build.fingerprint', 'Unknown')
    
    @property
    def kernel_version(self) -> str:
        return self._info.get('kernel_version', '')
    
    @property
    def build_date(self) -> str:
        return self._info.get('ro.build.date', '')
    
    @property
    def security_patch(self) -> str:
        return self._info.get('ro.build.version.security_patch', '')
    
    def get_repo_name(self) -> str:
        return f"{self.manufacturer}_{self.codename}_{self.android_version}_dump"
    
    def get_description(self) -> str:
        return f"{self.brand} {self.codename} Android {self.android_version} Firmware Dump"
    
    def get_all_info(self) -> Dict[str, str]:
        return {
            'brand': self.brand,
            'manufacturer': self.manufacturer,
            'codename': self.codename,
            'top_codename': self.top_codename,
            'platform': self.platform,
            'android_version': self.android_version,
            'fingerprint': self.fingerprint,
            'kernel_version': self.kernel_version,
            'build_date': self.build_date,
            'security_patch': self.security_patch
        }