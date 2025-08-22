import os
import re
from pathlib import Path
from typing import Tuple, Optional
from rich.console import Console

console = Console()

class FileDetector:
    def __init__(self, config):
        self.config = config
    
    def detect_file_type(self, filepath: Path) -> Tuple[str, str]:
        if not filepath.exists():
            return "unknown", "File not found"
        
        if filepath.is_dir():
            return self._detect_directory_type(filepath)
        
        filename = filepath.name
        extension = filepath.suffix.lower()
        
        with open(filepath, 'rb') as f:
            header = f.read(32)
        
        if header.startswith(b'OPPOENCRYPT!') or extension == '.ozip':
            return "oppo_ozip", "Oppo/Realme ozip encrypted firmware"
        
        if extension == '.ops':
            return "oppo_ops", "Oppo/Oneplus ops firmware"
        
        if extension == '.kdz':
            return "lg_kdz", "LG KDZ firmware"
        
        if filename.startswith('ruu_') and extension == '.exe':
            return "htc_ruu", "HTC RUU executable"
        
        if extension in ['.zip', '.rar', '.7z', '.tar']:
            return self._detect_archive_type(filepath)
        
        if extension == '.bin':
            return self._detect_bin_type(filepath, header)
        
        if 'payload.bin' in filename:
            return "ab_ota", "Android A/B OTA payload"
        
        if 'super' in filename and extension == '.img':
            return "super_img", "Android super partition image"
        
        if 'UPDATE.APP' in filename:
            return "huawei_update", "Huawei UPDATE.APP"
        
        if extension == '.pac':
            return "spreadtrum_pac", "Spreadtrum PAC firmware"
        
        if extension == '.nb0':
            return "qualcomm_nb0", "Qualcomm NB0 firmware"
        
        if 'chunk' in filename:
            return "chunk_images", "Chunked partition images"
        
        if extension == '.sin':
            return "sony_sin", "Sony SIN firmware"
        
        if filename.endswith('.new.dat') or filename.endswith('.new.dat.br') or filename.endswith('.new.dat.xz'):
            return "sparse_dat", "Sparse Android Data Transfer format"
        
        if extension in ['.img', '.ext4']:
            return "raw_image", "Raw partition image"
        
        return "unknown", f"Unknown file type: {extension}"
    
    def _detect_directory_type(self, dirpath: Path) -> Tuple[str, str]:
        files = list(dirpath.iterdir())
        
        has_archives = any(f.suffix.lower() in ['.zip', '.rar', '.7z', '.tar'] for f in files if f.is_file())
        if has_archives:
            return "archive_folder", "Directory containing firmware archives"
        
        has_system_files = any('system' in f.name for f in files)
        has_build_prop = any(f.name == 'build.prop' for f in files if f.is_file())
        has_new_dat = any(f.name.endswith('.new.dat') for f in files if f.is_file())
        has_payload = any(f.name == 'payload.bin' for f in files if f.is_file())
        has_super = any('super' in f.name for f in files if f.is_file())
        
        if has_system_files or has_build_prop or has_new_dat or has_payload or has_super:
            return "extracted_firmware", "Extracted firmware directory"
        
        return "unknown_dir", "Unknown directory type"
    
    def _detect_archive_type(self, filepath: Path) -> Tuple[str, str]:
        from .tools import ToolManager
        tool_manager = ToolManager(self.config)
        
        try:
            contents = tool_manager.list_archive_contents(filepath)
            if not contents:
                return "corrupted_archive", "Corrupted or encrypted archive"
            
            if 'payload.bin' in contents:
                return "ab_ota_archive", "Archive containing A/B OTA payload"
            
            if 'UPDATE.APP' in contents:
                return "huawei_archive", "Archive containing Huawei UPDATE.APP"
            
            if any(pattern in contents for pattern in ['system.new.dat', 'system.img', 'super.img']):
                return "firmware_archive", "Standard firmware archive"
            
            if '.ops' in contents:
                return "oppo_ops_archive", "Archive containing Oppo OPS firmware"
            
            if any(pattern in contents for pattern in ['chunk', 'system-p']):
                return "chunked_archive", "Archive with chunked images"
            
            return "generic_archive", "Generic compressed archive"
            
        except Exception:
            return "archive", "Compressed archive (detection failed)"
    
    def _detect_bin_type(self, filepath: Path, header: bytes) -> Tuple[str, str]:
        filename = filepath.name.lower()
        
        if 'boot' in filename:
            return "boot_img", "Boot partition image"
        
        if 'recovery' in filename:
            return "recovery_img", "Recovery partition image"
        
        if 'system' in filename:
            return "system_img", "System partition image"
        
        if header.startswith(b'ANDROID!'):
            return "android_img", "Android boot/recovery image"
        
        return "unknown_bin", "Unknown binary file"
    
    def get_file_info(self, filepath: Path) -> dict:
        file_type, description = self.detect_file_type(filepath)
        
        info = {
            'path': str(filepath),
            'name': filepath.name,
            'size': filepath.stat().st_size if filepath.exists() else 0,
            'type': file_type,
            'description': description,
            'extension': filepath.suffix.lower() if not filepath.is_dir() else None
        }
        
        return info
    
    def is_supported_format(self, filepath: Path) -> bool:
        file_type, _ = self.detect_file_type(filepath)
        
        supported_types = [
            "oppo_ozip", "oppo_ops", "lg_kdz", "htc_ruu", "firmware_archive",
            "ab_ota", "super_img", "huawei_update", "spreadtrum_pac", 
            "qualcomm_nb0", "chunk_images", "sony_sin", "sparse_dat",
            "raw_image", "extracted_firmware", "archive_folder"
        ]
        
        return file_type in supported_types