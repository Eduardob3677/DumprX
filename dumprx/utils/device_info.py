import re
from pathlib import Path
from typing import Dict, Optional
from rich.console import Console

class DeviceInfoExtractor:
    def __init__(self, config, console: Console):
        self.config = config
        self.console = console
    
    def extract_device_info(self, output_dir: Path) -> Optional[Dict[str, str]]:
        device_data = {}
        
        try:
            device_data.update(self._extract_from_build_prop(output_dir))
            device_data.update(self._extract_from_vendor_build_prop(output_dir))
            device_data.update(self._extract_modem_info(output_dir))
            device_data.update(self._extract_trustzone_info(output_dir))
            device_data.update(self._extract_kernel_info(output_dir))
            
            if device_data:
                self._generate_board_info(device_data, output_dir)
                self._generate_readme(device_data, output_dir)
                
                self.console.print("[green]✅ Device information extracted[/green]")
                return device_data
            else:
                self.console.print("[yellow]⚠️  Could not extract device information[/yellow]")
                return None
                
        except Exception as e:
            self.console.print(f"[red]❌ Error extracting device info: {str(e)}[/red]")
            return None
    
    def _extract_from_build_prop(self, output_dir: Path) -> Dict[str, str]:
        data = {}
        
        build_prop_paths = [
            output_dir / "system" / "build.prop",
            output_dir / "build.prop"
        ]
        
        for build_prop in build_prop_paths:
            if build_prop.exists():
                try:
                    content = build_prop.read_text(encoding='utf-8', errors='ignore')
                    
                    data['codename'] = self._extract_property(content, 'ro.product.device')
                    data['brand'] = self._extract_property(content, 'ro.product.brand')
                    data['model'] = self._extract_property(content, 'ro.product.model')
                    data['fingerprint'] = self._extract_property(content, 'ro.build.fingerprint')
                    data['platform'] = self._extract_property(content, 'ro.board.platform')
                    data['release'] = self._extract_property(content, 'ro.build.version.release')
                    data['api_level'] = self._extract_property(content, 'ro.build.version.sdk')
                    data['build_id'] = self._extract_property(content, 'ro.build.id')
                    data['incremental'] = self._extract_property(content, 'ro.build.version.incremental')
                    data['security_patch'] = self._extract_property(content, 'ro.build.version.security_patch')
                    
                    break
                except Exception:
                    continue
        
        return {k: v for k, v in data.items() if v}
    
    def _extract_from_vendor_build_prop(self, output_dir: Path) -> Dict[str, str]:
        data = {}
        
        vendor_build_prop = output_dir / "vendor" / "build.prop"
        if vendor_build_prop.exists():
            try:
                content = vendor_build_prop.read_text(encoding='utf-8', errors='ignore')
                data['vendor_build_date'] = self._extract_property(content, 'ro.vendor.build.date.utc')
            except Exception:
                pass
        
        return {k: v for k, v in data.items() if v}
    
    def _extract_modem_info(self, output_dir: Path) -> Dict[str, str]:
        data = {}
        
        modem_files = list(output_dir.glob("modem*"))
        if modem_files:
            try:
                import subprocess
                for modem_file in modem_files:
                    if modem_file.is_file():
                        result = subprocess.run([
                            'strings', str(modem_file)
                        ], capture_output=True, text=True)
                        
                        for line in result.stdout.splitlines():
                            if 'QC_IMAGE_VERSION_STRING=MPSS.' in line:
                                version = line.split('QC_IMAGE_VERSION_STRING=MPSS.')[1][3:]
                                data['modem_version'] = version
                                break
            except Exception:
                pass
        
        return {k: v for k, v in data.items() if v}
    
    def _extract_trustzone_info(self, output_dir: Path) -> Dict[str, str]:
        data = {}
        
        tz_files = list(output_dir.glob("tz*"))
        if tz_files:
            try:
                import subprocess
                for tz_file in tz_files:
                    if tz_file.is_file():
                        result = subprocess.run([
                            'strings', str(tz_file)
                        ], capture_output=True, text=True)
                        
                        for line in result.stdout.splitlines():
                            if 'QC_IMAGE_VERSION_STRING' in line:
                                data['trustzone_version'] = line.split('QC_IMAGE_VERSION_STRING')[1]
                                break
            except Exception:
                pass
        
        return {k: v for k, v in data.items() if v}
    
    def _extract_kernel_info(self, output_dir: Path) -> Dict[str, str]:
        data = {}
        
        ikconfig_file = output_dir / "bootRE" / "ikconfig"
        if ikconfig_file.exists():
            try:
                content = ikconfig_file.read_text(encoding='utf-8', errors='ignore')
                match = re.search(r'Kernel Configuration.*?(\d+\.\d+\.\d+)', content)
                if match:
                    data['kernel_version'] = match.group(1)
            except Exception:
                pass
        
        return {k: v for k, v in data.items() if v}
    
    def _extract_property(self, content: str, prop_name: str) -> Optional[str]:
        pattern = rf'^{re.escape(prop_name)}=(.*)$'
        match = re.search(pattern, content, re.MULTILINE)
        return match.group(1).strip() if match else None
    
    def _generate_board_info(self, device_data: Dict[str, str], output_dir: Path):
        board_info_lines = []
        
        if 'modem_version' in device_data:
            board_info_lines.append(f"require version-baseband={device_data['modem_version']}")
        
        if 'trustzone_version' in device_data:
            board_info_lines.append(f"require version-trustzone{device_data['trustzone_version']}")
        
        if 'vendor_build_date' in device_data:
            board_info_lines.append(f"require version-vendor={device_data['vendor_build_date']}")
        
        if board_info_lines:
            board_info_file = output_dir / "board-info.txt"
            board_info_file.write_text('\n'.join(sorted(set(board_info_lines))) + '\n')
    
    def _generate_readme(self, device_data: Dict[str, str], output_dir: Path):
        readme_content = f"""# {device_data.get('brand', 'Unknown')} {device_data.get('model', 'Unknown')}

## Device Information
- **Device**: {device_data.get('codename', 'Unknown')}
- **Brand**: {device_data.get('brand', 'Unknown')}  
- **Model**: {device_data.get('model', 'Unknown')}
- **Platform**: {device_data.get('platform', 'Unknown')}
- **Android Version**: {device_data.get('release', 'Unknown')}
- **API Level**: {device_data.get('api_level', 'Unknown')}
- **Build ID**: {device_data.get('build_id', 'Unknown')}
- **Security Patch**: {device_data.get('security_patch', 'Unknown')}

## Build Information
- **Fingerprint**: `{device_data.get('fingerprint', 'Unknown')}`
- **Incremental**: {device_data.get('incremental', 'Unknown')}
"""

        if 'kernel_version' in device_data:
            readme_content += f"- **Kernel Version**: {device_data['kernel_version']}\n"

        readme_content += """
## Extraction Information
This firmware was extracted using [DumprX](https://github.com/Eduardob3677/DumprX)

### Files Included
"""

        all_files = []
        for item in output_dir.rglob("*"):
            if item.is_file() and item.name not in ['README.md', 'all_files.txt']:
                relative_path = item.relative_to(output_dir)
                all_files.append(str(relative_path))

        all_files.sort()
        
        for file_path in all_files[:50]:  # Limit to first 50 files
            readme_content += f"- {file_path}\n"
        
        if len(all_files) > 50:
            readme_content += f"\n... and {len(all_files) - 50} more files\n"

        readme_file = output_dir / "README.md"
        readme_file.write_text(readme_content)
        
        all_files_txt = output_dir / "all_files.txt"
        all_files_txt.write_text('\n'.join(all_files) + '\n')