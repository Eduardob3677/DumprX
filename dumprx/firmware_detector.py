#!/usr/bin/env python3

import os
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

from rich.console import Console

from .utils import run_command, get_file_extension

console = Console()

class FirmwareDetector:
    def __init__(self, tool_manager):
        self.tool_manager = tool_manager
        self.supported_formats = {
            'ozip': self._detect_ozip,
            'ops': self._detect_ops, 
            'kdz': self._detect_kdz,
            'zip': self._detect_archive,
            'rar': self._detect_archive,
            '7z': self._detect_archive,
            'tar': self._detect_archive,
            'gz': self._detect_archive,
            'tgz': self._detect_archive,
            'bin': self._detect_binary,
            'img': self._detect_image,
            'nb0': self._detect_nb0,
            'pac': self._detect_pac,
            'sin': self._detect_sin,
            'exe': self._detect_ruu
        }
    
    def detect_firmware_type(self, filepath: Path) -> Dict[str, Any]:
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        if filepath.is_dir():
            return self._detect_directory(filepath)
        
        extension = get_file_extension(filepath).lower()
        
        # Special case for files without extension
        if not extension:
            return self._detect_by_content(filepath)
        
        # Check by extension first
        if extension in self.supported_formats:
            return self.supported_formats[extension](filepath)
        
        # Fallback to content detection
        return self._detect_by_content(filepath)
    
    def _detect_ozip(self, filepath: Path) -> Dict[str, Any]:
        try:
            # Check OZIP magic header
            with open(filepath, 'rb') as f:
                header = f.read(12).replace(b'\x00', b'').decode('ascii', errors='ignore')
                if header == "OPPOENCRYPT!":
                    return {
                        'type': 'ozip',
                        'format': 'Oppo/Realme OZIP',
                        'needs_decryption': True
                    }
        except:
            pass
        
        return self._detect_archive(filepath)
    
    def _detect_ops(self, filepath: Path) -> Dict[str, Any]:
        return {
            'type': 'ops',
            'format': 'Oppo/OnePlus OPS',
            'needs_decryption': True
        }
    
    def _detect_kdz(self, filepath: Path) -> Dict[str, Any]:
        return {
            'type': 'kdz', 
            'format': 'LG KDZ',
            'needs_extraction': True
        }
    
    def _detect_archive(self, filepath: Path) -> Dict[str, Any]:
        extension = get_file_extension(filepath).lower()
        
        # Check for special contents in archives
        bin_7zz = self.tool_manager.get_tool_path("7zz")
        
        try:
            result = run_command([str(bin_7zz), "l", "-ba", str(filepath)], 
                               capture_output=True, check=False)
            contents = result.stdout if result.returncode == 0 else ""
            
            if "payload.bin" in contents:
                return {
                    'type': 'ota_payload',
                    'format': 'Android OTA Payload',
                    'archive_type': extension
                }
            elif "UPDATE.APP" in contents:
                return {
                    'type': 'huawei_update',
                    'format': 'Huawei UPDATE.APP',
                    'archive_type': extension
                }
            elif any(ops in contents for ops in ['.ops']):
                return {
                    'type': 'ops_archive',
                    'format': 'OPS Archive',
                    'archive_type': extension
                }
        except:
            pass
        
        return {
            'type': 'archive',
            'format': f'{extension.upper()} Archive',
            'archive_type': extension
        }
    
    def _detect_binary(self, filepath: Path) -> Dict[str, Any]:
        filename = filepath.name.lower()
        
        if "system" in filename:
            return {
                'type': 'system_image',
                'format': 'System Binary Image'
            }
        elif "payload" in filename:
            return {
                'type': 'payload',
                'format': 'Android OTA Payload'
            }
        elif "update.app" in filename:
            return {
                'type': 'huawei_update',
                'format': 'Huawei UPDATE.APP'
            }
        
        return {
            'type': 'binary',
            'format': 'Binary File'
        }
    
    def _detect_image(self, filepath: Path) -> Dict[str, Any]:
        filename = filepath.name.lower()
        
        if "super" in filename:
            return {
                'type': 'super_image',
                'format': 'Android Super Image'
            }
        elif any(part in filename for part in ['system', 'vendor', 'boot', 'recovery']):
            return {
                'type': 'partition_image',
                'format': 'Android Partition Image'
            }
        
        return {
            'type': 'image',
            'format': 'Disk Image'
        }
    
    def _detect_nb0(self, filepath: Path) -> Dict[str, Any]:
        return {
            'type': 'nb0',
            'format': 'Nokia NB0 Firmware'
        }
    
    def _detect_pac(self, filepath: Path) -> Dict[str, Any]:
        return {
            'type': 'pac',
            'format': 'Spreadtrum PAC'
        }
    
    def _detect_sin(self, filepath: Path) -> Dict[str, Any]:
        return {
            'type': 'sin',
            'format': 'Sony SIN'
        }
    
    def _detect_ruu(self, filepath: Path) -> Dict[str, Any]:
        if filepath.name.lower().startswith('ruu_'):
            return {
                'type': 'ruu',
                'format': 'HTC RUU'
            }
        
        return {
            'type': 'executable',
            'format': 'Executable File'
        }
    
    def _detect_directory(self, dirpath: Path) -> Dict[str, Any]:
        # Check for firmware files in directory
        firmware_indicators = [
            'system.new.dat', 'system.img', 'payload.bin', 
            'UPDATE.APP', 'super.img', 'build.prop'
        ]
        
        for indicator in firmware_indicators:
            if any(dirpath.glob(f"**/{indicator}")):
                return {
                    'type': 'firmware_directory',
                    'format': 'Firmware Directory',
                    'contains': indicator
                }
        
        # Check for archives in directory
        archives = list(dirpath.glob("*.zip")) + list(dirpath.glob("*.rar")) + \
                  list(dirpath.glob("*.7z")) + list(dirpath.glob("*.tar"))
        
        if archives:
            return {
                'type': 'archive_directory',
                'format': 'Directory with Archives',
                'archives': [a.name for a in archives]
            }
        
        return {
            'type': 'directory',
            'format': 'Directory'
        }
    
    def _detect_by_content(self, filepath: Path) -> Dict[str, Any]:
        try:
            with open(filepath, 'rb') as f:
                header = f.read(16)
                
                # Check various magic headers
                if header.startswith(b'OPPOENCRYPT!'):
                    return {
                        'type': 'ozip',
                        'format': 'Oppo OZIP (detected by header)'
                    }
                elif header.startswith(b'PK'):
                    return {
                        'type': 'zip',
                        'format': 'ZIP Archive (detected by header)'
                    }
                elif header.startswith(b'\x37\x7a\xbc\xaf\x27\x1c'):
                    return {
                        'type': '7z',
                        'format': '7-Zip Archive (detected by header)'
                    }
        except:
            pass
        
        return {
            'type': 'unknown',
            'format': 'Unknown Format'
        }