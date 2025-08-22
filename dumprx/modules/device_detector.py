import os
import re
from pathlib import Path

class DeviceDetector:
    def __init__(self, console, verbose=False):
        self.console = console
        self.verbose = verbose
    
    def detect_device(self, extracted_path):
        self.console.print("[blue]🔍 Detecting device information...[/blue]")
        
        device_info = {}
        
        build_prop_files = [
            "system/build.prop",
            "system/system/build.prop",
            "vendor/build.prop",
            "product/build.prop"
        ]
        
        for build_prop in build_prop_files:
            build_prop_path = extracted_path / build_prop
            if build_prop_path.exists():
                props = self._parse_build_prop(build_prop_path)
                device_info.update(props)
                break
        
        recovery_info = self._detect_recovery_info(extracted_path)
        if recovery_info:
            device_info.update(recovery_info)
        
        bootimg_info = self._detect_bootimg_info(extracted_path)
        if bootimg_info:
            device_info.update(bootimg_info)
        
        if device_info:
            self.console.print("[green]✅ Device information detected[/green]")
        else:
            self.console.print("[yellow]⚠️  Could not detect device information[/yellow]")
        
        return device_info
    
    def _parse_build_prop(self, build_prop_path):
        props = {}
        
        try:
            with open(build_prop_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        props[key] = value
            
            device_info = {}
            
            if 'ro.product.brand' in props:
                device_info['brand'] = props['ro.product.brand']
            elif 'ro.product.manufacturer' in props:
                device_info['brand'] = props['ro.product.manufacturer']
            
            if 'ro.product.model' in props:
                device_info['model'] = props['ro.product.model']
            elif 'ro.product.name' in props:
                device_info['model'] = props['ro.product.name']
            
            if 'ro.product.device' in props:
                device_info['codename'] = props['ro.product.device']
            elif 'ro.build.product' in props:
                device_info['codename'] = props['ro.build.product']
            
            if 'ro.build.version.release' in props:
                device_info['android_version'] = props['ro.build.version.release']
            
            if 'ro.build.version.sdk' in props:
                device_info['api_level'] = props['ro.build.version.sdk']
            
            if 'ro.build.fingerprint' in props:
                device_info['fingerprint'] = props['ro.build.fingerprint']
            
            if 'ro.build.date' in props:
                device_info['build_date'] = props['ro.build.date']
            
            return device_info
            
        except Exception as e:
            if self.verbose:
                self.console.print(f"[yellow]⚠️  Error parsing build.prop: {str(e)}[/yellow]")
            return {}
    
    def _detect_recovery_info(self, extracted_path):
        recovery_info = {}
        
        recovery_files = list(extracted_path.rglob("recovery*"))
        if recovery_files:
            recovery_info['has_recovery'] = True
        
        twrp_files = list(extracted_path.rglob("*twrp*"))
        if twrp_files:
            recovery_info['recovery_type'] = 'TWRP'
        
        return recovery_info
    
    def _detect_bootimg_info(self, extracted_path):
        bootimg_info = {}
        
        boot_files = list(extracted_path.rglob("boot*"))
        if boot_files:
            bootimg_info['has_boot'] = True
            
            for boot_file in boot_files:
                if boot_file.suffix in ['.img', '.bin']:
                    kernel_version = self._extract_kernel_version(boot_file)
                    if kernel_version:
                        bootimg_info['kernel_version'] = kernel_version
                        break
        
        return bootimg_info
    
    def _extract_kernel_version(self, boot_file):
        try:
            with open(boot_file, 'rb') as f:
                data = f.read(1024 * 1024)  
                
                kernel_pattern = rb'Linux version [\d\.]+'
                match = re.search(kernel_pattern, data)
                if match:
                    return match.group(0).decode('utf-8', errors='ignore')
        except Exception as e:
            if self.verbose:
                self.console.print(f"[yellow]⚠️  Error extracting kernel version: {str(e)}[/yellow]")
        
        return None