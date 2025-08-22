import re
from pathlib import Path
from typing import Dict, Optional, List
from dumprx.utils.logging import logger

class DeviceDetector:
    def __init__(self):
        self.device_info = {}
        
    def detect_from_build_props(self, base_path: Path) -> Dict[str, str]:
        info = {}
        
        build_prop_paths = [
            base_path / "system" / "build.prop",
            base_path / "system" / "system" / "build.prop",
            base_path / "vendor" / "build.prop",
        ]
        
        for prop_file in build_prop_paths:
            if prop_file.exists():
                info.update(self._parse_build_prop(prop_file))
                
        return info
    
    def _parse_build_prop(self, prop_file: Path) -> Dict[str, str]:
        info = {}
        try:
            content = prop_file.read_text(encoding='utf-8', errors='ignore')
            
            patterns = {
                'brand': r'ro\.product\.brand=(.+)',
                'manufacturer': r'ro\.product\.manufacturer=(.+)',
                'model': r'ro\.product\.model=(.+)',
                'device': r'ro\.product\.device=(.+)',
                'codename': r'ro\.product\.name=(.+)',
                'fingerprint': r'ro\.build\.fingerprint=(.+)',
                'version_release': r'ro\.build\.version\.release=(.+)',
                'version_sdk': r'ro\.build\.version\.sdk=(.+)',
                'security_patch': r'ro\.build\.version\.security_patch=(.+)',
                'incremental': r'ro\.build\.version\.incremental=(.+)',
                'tags': r'ro\.build\.tags=(.+)',
                'flavor': r'ro\.build\.flavor=(.+)',
                'id': r'ro\.build\.id=(.+)',
                'abilist': r'ro\.product\.cpu\.abilist=(.+)',
                'locale': r'ro\.product\.locale=(.+)',
                'density': r'ro\.sf\.lcd_density=(.+)',
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, content, re.MULTILINE)
                if match and not info.get(key):
                    info[key] = match.group(1).strip()
                    
        except Exception as e:
            logger.warning(f"Error parsing {prop_file}: {e}")
            
        return info
    
    def detect_partitions(self, base_path: Path) -> List[str]:
        detected = []
        
        from dumprx.core.config import config
        
        for partition in config.partitions:
            partition_paths = [
                base_path / f"{partition}.img",
                base_path / f"{partition}.new.dat",
                base_path / f"{partition}.new.dat.br",
                base_path / f"{partition}.new.dat.xz",
                base_path / f"{partition}",
            ]
            
            if any(path.exists() for path in partition_paths):
                detected.append(partition)
                
        return detected
    
    def detect_firmware_type(self, file_path: Path) -> str:
        filename = file_path.name.lower()
        
        if filename.endswith('.kdz'):
            return 'lg_kdz'
        elif filename.endswith('.ozip'):
            return 'oppo_ozip'
        elif filename.endswith('.ofp'):
            return 'oppo_ofp'
        elif filename.endswith('.ops'):
            return 'oppo_ops'
        elif 'payload.bin' in filename:
            return 'payload'
        elif filename.startswith('ruu_') and filename.endswith('.exe'):
            return 'htc_ruu'
        elif filename == 'update.app':
            return 'huawei_update'
        elif filename.endswith('.nb0'):
            return 'nokia_nb0'
        elif filename.endswith('.pac'):
            return 'spreadtrum_pac'
        elif filename.endswith('.sin'):
            return 'sony_sin'
        elif 'super' in filename and filename.endswith('.img'):
            return 'super_img'
        elif any(filename.endswith(ext) for ext in ['.zip', '.rar', '.7z', '.tar', '.tar.gz', '.tgz']):
            return 'archive'
        elif filename.endswith('.new.dat'):
            return 'android_dat'
        elif filename.endswith('.img'):
            return 'raw_img'
        else:
            return 'unknown'
    
    def detect_kernel_version(self, base_path: Path) -> Optional[str]:
        ikconfig_path = base_path / "bootRE" / "ikconfig"
        if ikconfig_path.exists():
            try:
                content = ikconfig_path.read_text()
                match = re.search(r'Kernel Configuration.*?(\d+\.\d+\.\d+)', content)
                if match:
                    return match.group(1)
            except Exception:
                pass
        return None
    
    def generate_description(self, info: Dict[str, str]) -> str:
        parts = []
        
        if info.get('flavor') and info.get('release') and info.get('id') and info.get('incremental') and info.get('tags'):
            parts.extend([info['flavor'], info['release'], info['id'], info['incremental'], info['tags']])
        elif info.get('incremental'):
            parts.append(info['incremental'])
        elif info.get('codename'):
            parts.append(info['codename'])
            
        return ' '.join(parts) if parts else 'Unknown'