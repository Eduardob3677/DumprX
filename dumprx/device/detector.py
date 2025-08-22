import os
import re
import json
from pathlib import Path
from typing import Dict, Optional, List


class DeviceDetector:
    def __init__(self):
        self.device_info = {}
    
    def detect_from_firmware(self, firmware_dir: Path) -> Dict[str, str]:
        device_info = {}
        
        device_info.update(self._detect_from_build_prop(firmware_dir))
        device_info.update(self._detect_from_fstab(firmware_dir))
        device_info.update(self._detect_from_boot_img(firmware_dir))
        device_info.update(self._detect_treble_support(firmware_dir))
        
        return device_info
    
    def _detect_from_build_prop(self, firmware_dir: Path) -> Dict[str, str]:
        info = {}
        
        build_prop_paths = [
            firmware_dir / "system/build.prop",
            firmware_dir / "system/system/build.prop", 
            firmware_dir / "build.prop"
        ]
        
        for build_prop in build_prop_paths:
            if build_prop.exists():
                info.update(self._parse_build_prop(build_prop))
                break
        
        return info
    
    def _parse_build_prop(self, build_prop_path: Path) -> Dict[str, str]:
        info = {}
        
        try:
            with open(build_prop_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        
                        if key == 'ro.product.device':
                            info['device'] = value
                        elif key == 'ro.build.product':
                            info['product'] = value
                        elif key == 'ro.product.brand':
                            info['brand'] = value
                        elif key == 'ro.product.manufacturer':
                            info['manufacturer'] = value
                        elif key == 'ro.product.model':
                            info['model'] = value
                        elif key == 'ro.build.version.release':
                            info['android_version'] = value
                        elif key == 'ro.build.version.sdk':
                            info['sdk_version'] = value
                        elif key == 'ro.build.version.codename':
                            info['codename'] = value
                        elif key == 'ro.build.fingerprint':
                            info['fingerprint'] = value
                        elif key == 'ro.build.description':
                            info['description'] = value
                        elif key == 'ro.product.cpu.abi':
                            info['arch'] = value
                        elif key == 'ro.build.id':
                            info['build_id'] = value
                        elif key == 'ro.build.date':
                            info['build_date'] = value
        except Exception:
            pass
        
        return info
    
    def _detect_from_fstab(self, firmware_dir: Path) -> Dict[str, str]:
        info = {}
        
        fstab_paths = [
            firmware_dir / "fstab",
            firmware_dir / "system/etc/fstab",
            firmware_dir / "vendor/etc/fstab",
            firmware_dir / "recovery/root/etc/fstab"
        ]
        
        for fstab_dir in fstab_paths:
            if fstab_dir.is_dir():
                for fstab_file in fstab_dir.glob("fstab.*"):
                    info.update(self._parse_fstab(fstab_file))
                    break
            elif fstab_dir.is_file():
                info.update(self._parse_fstab(fstab_dir))
        
        return info
    
    def _parse_fstab(self, fstab_path: Path) -> Dict[str, str]:
        info = {}
        
        try:
            with open(fstab_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                if '/system' in content:
                    info['has_system'] = 'true'
                if '/vendor' in content:
                    info['has_vendor'] = 'true'
                if '/odm' in content:
                    info['has_odm'] = 'true'
                if '/product' in content:
                    info['has_product'] = 'true'
                if '/system_ext' in content:
                    info['has_system_ext'] = 'true'
        except Exception:
            pass
        
        return info
    
    def _detect_from_boot_img(self, firmware_dir: Path) -> Dict[str, str]:
        info = {}
        
        boot_files = [
            firmware_dir / "boot.img",
            firmware_dir / "recovery.img",
            firmware_dir / "vendor_boot.img"
        ]
        
        for boot_file in boot_files:
            if boot_file.exists():
                info['has_boot'] = 'true'
                
                if boot_file.name == 'vendor_boot.img':
                    info['has_vendor_boot'] = 'true'
                if boot_file.name == 'recovery.img':
                    info['has_recovery'] = 'true'
                    
                info.update(self._analyze_boot_header(boot_file))
                break
        
        return info
    
    def _analyze_boot_header(self, boot_file: Path) -> Dict[str, str]:
        info = {}
        
        try:
            with open(boot_file, 'rb') as f:
                header = f.read(2048)
                
                if b'ANDROID!' in header:
                    info['boot_format'] = 'android'
                elif b'VNDRBOOT' in header:
                    info['boot_format'] = 'vndrboot'
                
                if len(header) >= 648:
                    version = int.from_bytes(header[40:44], 'little')
                    info['boot_version'] = str(version)
        except Exception:
            pass
        
        return info
    
    def _detect_treble_support(self, firmware_dir: Path) -> Dict[str, str]:
        info = {}
        
        treble_indicators = [
            firmware_dir / "vendor",
            firmware_dir / "system/vendor",
            firmware_dir / "system/system/vendor"
        ]
        
        for treble_path in treble_indicators:
            if treble_path.exists() and treble_path.is_dir():
                if any(treble_path.glob("*")):
                    info['treble_support'] = 'true'
                    break
        else:
            info['treble_support'] = 'false'
        
        return info
    
    def generate_device_tree_info(self, device_info: Dict[str, str]) -> Dict[str, str]:
        tree_info = {}
        
        if 'device' in device_info:
            tree_info['DEVICE'] = device_info['device']
        if 'manufacturer' in device_info:
            tree_info['VENDOR'] = device_info['manufacturer'].lower()
        if 'brand' in device_info:
            tree_info['BRAND'] = device_info['brand']
        if 'model' in device_info:
            tree_info['MODEL'] = device_info['model']
        if 'arch' in device_info:
            tree_info['ARCH'] = 'arm64' if 'arm64' in device_info['arch'] else 'arm'
        
        return tree_info