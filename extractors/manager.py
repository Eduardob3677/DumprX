import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from extractors.ozip import OzipExtractor
from extractors.ops import OpsExtractor
from extractors.kdz import KdzExtractor
from extractors.archive import ArchiveExtractor
from extractors.archive import SuperImageExtractor, PayloadExtractor
from utils.console import Console


class ExtractorManager:
    def __init__(self, output_dir: Path, utils_dir: Path):
        self.output_dir = Path(output_dir)
        self.utils_dir = Path(utils_dir)
        self.console = Console()
        
        self.extractors = {
            'ozip': OzipExtractor(utils_dir),
            'ops': OpsExtractor(utils_dir),
            'kdz': KdzExtractor(utils_dir),
            'archive': ArchiveExtractor(utils_dir),
            'super': SuperImageExtractor(utils_dir),
            'payload': PayloadExtractor(utils_dir)
        }
    
    def extract(self, firmware_path: Path) -> Path:
        self.console.info(f"Detecting firmware type: {firmware_path.name}")
        
        if firmware_path.is_dir():
            return self._handle_directory(firmware_path)
        
        file_type = self._detect_file_type(firmware_path)
        self.console.info(f"Detected type: {file_type}")
        
        extractor = self.extractors.get(file_type)
        if not extractor:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        return extractor.extract(firmware_path, self.output_dir)
    
    def _detect_file_type(self, firmware_path: Path) -> str:
        file_name = firmware_path.name.lower()
        extension = firmware_path.suffix.lower()
        
        if self._is_ozip_file(firmware_path):
            return 'ozip'
        elif extension == '.ops':
            return 'ops'
        elif extension == '.kdz':
            return 'kdz'
        elif 'super' in file_name and '.img' in file_name:
            return 'super'
        elif file_name == 'payload.bin':
            return 'payload'
        elif extension in ['.zip', '.rar', '.7z', '.tar']:
            return 'archive'
        else:
            return 'archive'
    
    def _is_ozip_file(self, firmware_path: Path) -> bool:
        try:
            with open(firmware_path, 'rb') as f:
                header = f.read(12)
                return header.replace(b'\\0', b'') == b'OPPOENCRYPT!'
        except Exception:
            return firmware_path.suffix.lower() == '.ozip'
    
    def _handle_directory(self, dir_path: Path) -> Path:
        self.console.info("Processing directory")
        
        archive_files = []
        for pattern in ['*.zip', '*.rar', '*.7z', '*.tar']:
            archive_files.extend(dir_path.glob(pattern))
        
        if len(archive_files) == 1:
            return self.extract(archive_files[0])
        elif len(archive_files) > 1:
            raise ValueError(f"Multiple archive files found in {dir_path}")
        
        supported_files = []
        for pattern in ['*.img', '*.dat', '*.bin', '*.pac', '*.nb0', '*.sin']:
            supported_files.extend(dir_path.glob(pattern))
        
        if supported_files:
            return dir_path
        
        raise ValueError(f"No supported files found in {dir_path}")