"""
Device information extraction and management.

Extracts device information from firmware build properties and other sources.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass


@dataclass
class DeviceInfo:
    """Device information extracted from firmware."""
    
    brand: Optional[str] = None
    model: Optional[str] = None
    device: Optional[str] = None
    codename: Optional[str] = None
    flavor: Optional[str] = None
    release: Optional[str] = None
    build_id: Optional[str] = None
    tags: Optional[str] = None
    platform: Optional[str] = None
    security_patch: Optional[str] = None
    bootloader: Optional[str] = None
    baseband: Optional[str] = None
    fingerprint: Optional[str] = None
    incremental: Optional[str] = None
    build_date: Optional[str] = None
    
    @classmethod
    def from_build_props(cls, output_dir: Union[str, Path]) -> "DeviceInfo":
        """
        Extract device information from build.prop files.
        
        Args:
            output_dir: Directory containing extracted firmware files
            
        Returns:
            DeviceInfo instance with extracted information
        """
        output_path = Path(output_dir)
        device_info = cls()
        
        # Find all build.prop files
        build_prop_files = []
        
        # Search in common locations
        for pattern in [
            "system/build.prop",
            "system/system/build.prop", 
            "vendor/build.prop",
            "product/build.prop",
            "system_ext/build.prop",
            "odm/build.prop",
        ]:
            prop_file = output_path / pattern
            if prop_file.exists():
                build_prop_files.append(prop_file)
        
        # Extract properties from all found files
        all_props = {}
        for prop_file in build_prop_files:
            props = device_info._parse_build_prop(prop_file)
            all_props.update(props)
        
        # Extract device information with fallbacks
        device_info.brand = device_info._get_prop_with_fallbacks(all_props, [
            "ro.product.brand",
            "ro.product.system.brand", 
            "ro.product.vendor.brand",
            "ro.vendor.product.brand"
        ])
        
        device_info.model = device_info._get_prop_with_fallbacks(all_props, [
            "ro.product.model",
            "ro.product.system.model",
            "ro.product.vendor.model", 
            "ro.vendor.product.model"
        ])
        
        device_info.device = device_info._get_prop_with_fallbacks(all_props, [
            "ro.product.device",
            "ro.product.system.device",
            "ro.product.vendor.device",
            "ro.vendor.product.device"
        ])
        
        device_info.codename = device_info._get_prop_with_fallbacks(all_props, [
            "ro.build.product",
            "ro.product.name",
            "ro.product.system.name"
        ])
        
        device_info.flavor = device_info._get_prop_with_fallbacks(all_props, [
            "ro.build.flavor",
            "ro.vendor.build.flavor",
            "ro.system.build.flavor",
            "ro.build.type"
        ])
        
        device_info.release = device_info._get_prop_with_fallbacks(all_props, [
            "ro.build.version.release",
            "ro.vendor.build.version.release", 
            "ro.system.build.version.release"
        ])
        
        device_info.build_id = device_info._get_prop_with_fallbacks(all_props, [
            "ro.build.id",
            "ro.vendor.build.id",
            "ro.system.build.id"
        ])
        
        device_info.tags = device_info._get_prop_with_fallbacks(all_props, [
            "ro.build.tags",
            "ro.vendor.build.tags",
            "ro.system.build.tags"
        ])
        
        device_info.platform = device_info._get_prop_with_fallbacks(all_props, [
            "ro.board.platform",
            "ro.hardware.platform",
            "ro.product.board"
        ])
        
        device_info.security_patch = device_info._get_prop_with_fallbacks(all_props, [
            "ro.build.version.security_patch",
            "ro.vendor.build.security_patch"
        ])
        
        device_info.bootloader = device_info._get_prop_with_fallbacks(all_props, [
            "ro.bootloader",
            "ro.boot.bootloader"
        ])
        
        device_info.baseband = device_info._get_prop_with_fallbacks(all_props, [
            "ro.baseband",
            "ro.boot.baseband"
        ])
        
        device_info.fingerprint = device_info._get_prop_with_fallbacks(all_props, [
            "ro.build.fingerprint",
            "ro.vendor.build.fingerprint",
            "ro.system.build.fingerprint"
        ])
        
        device_info.incremental = device_info._get_prop_with_fallbacks(all_props, [
            "ro.build.version.incremental",
            "ro.vendor.build.version.incremental"
        ])
        
        device_info.build_date = device_info._get_prop_with_fallbacks(all_props, [
            "ro.build.date",
            "ro.vendor.build.date"
        ])
        
        return device_info
    
    def _parse_build_prop(self, prop_file: Path) -> Dict[str, str]:
        """Parse a build.prop file and return key-value pairs."""
        props = {}
        
        try:
            with open(prop_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse property line
                    if '=' in line:
                        key, value = line.split('=', 1)
                        props[key.strip()] = value.strip()
        
        except Exception:
            # Ignore errors reading individual files
            pass
        
        return props
    
    def _get_prop_with_fallbacks(self, props: Dict[str, str], keys: List[str]) -> Optional[str]:
        """Get property value with fallback keys."""
        for key in keys:
            value = props.get(key)
            if value:
                return value
        return None
    
    def to_dict(self) -> Dict[str, Optional[str]]:
        """Convert device info to dictionary."""
        return {
            'brand': self.brand,
            'model': self.model,
            'device': self.device,
            'codename': self.codename,
            'flavor': self.flavor,
            'release': self.release,
            'build_id': self.build_id,
            'tags': self.tags,
            'platform': self.platform,
            'security_patch': self.security_patch,
            'bootloader': self.bootloader,
            'baseband': self.baseband,
            'fingerprint': self.fingerprint,
            'incremental': self.incremental,
            'build_date': self.build_date,
        }
    
    def get_repo_name(self) -> str:
        """Generate a repository name based on device information."""
        parts = []
        
        if self.brand:
            parts.append(self.brand.lower())
        
        if self.device or self.codename:
            device_name = self.device or self.codename
            parts.append(device_name.lower())
        
        if self.build_id:
            parts.append(self.build_id)
        
        if not parts:
            parts = ["unknown_device"]
        
        return "_".join(parts)
    
    def get_commit_message(self) -> str:
        """Generate a commit message based on device information."""
        if self.brand and self.model and self.build_id:
            return f"{self.brand} {self.model}: Add firmware dump {self.build_id}"
        elif self.device and self.build_id:
            return f"{self.device}: Add firmware dump {self.build_id}"
        elif self.fingerprint:
            return f"Add firmware dump: {self.fingerprint}"
        else:
            return "Add firmware dump"
    
    def __str__(self) -> str:
        """String representation of device info."""
        parts = []
        
        if self.brand and self.model:
            parts.append(f"{self.brand} {self.model}")
        elif self.brand:
            parts.append(self.brand)
        elif self.model:
            parts.append(self.model)
        
        if self.device:
            parts.append(f"({self.device})")
        
        if self.release:
            parts.append(f"Android {self.release}")
        
        if self.build_id:
            parts.append(f"Build {self.build_id}")
        
        return " ".join(parts) if parts else "Unknown Device"