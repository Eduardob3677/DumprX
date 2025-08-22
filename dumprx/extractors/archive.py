import os
import subprocess
import shutil
from pathlib import Path
from dumprx.core.config import Config
from dumprx.utils.console import console, info, warning

class ArchiveExtractor:
    def __init__(self, config: Config):
        self.config = config
        self.utils_dir = Path(__file__).parent.parent.parent / "utils"
    
    def extract(self, archive_path: str, output_dir: str) -> str:
        """Extract archive files using 7zz or appropriate tool"""
        file_extension = Path(archive_path).suffix.lower()
        
        if file_extension in ['.zip', '.rar', '.7z']:
            return self._extract_with_7zz(archive_path, output_dir)
        elif file_extension in ['.tar', '.gz', '.tgz']:
            return self._extract_tar(archive_path, output_dir)
        else:
            warning(f"Unknown archive format: {file_extension}")
            return self._extract_with_7zz(archive_path, output_dir)
    
    def _extract_with_7zz(self, archive_path: str, output_dir: str) -> str:
        """Extract using 7zz"""
        bin_7zz = self._get_7zz_binary()
        
        info(f"Extracting {archive_path} with 7zz")
        
        cmd = [bin_7zz, 'x', archive_path, f'-o{output_dir}', '-y']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"7zz extraction failed: {result.stderr}")
        
        return output_dir
    
    def _extract_tar(self, archive_path: str, output_dir: str) -> str:
        """Extract tar archives"""
        info(f"Extracting {archive_path} with tar")
        
        cmd = ['tar', '-xf', archive_path, '-C', output_dir]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"tar extraction failed: {result.stderr}")
        
        return output_dir
    
    def _get_7zz_binary(self) -> str:
        """Get 7zz binary path"""
        try:
            subprocess.run(['7zz'], capture_output=True)
            return '7zz'
        except FileNotFoundError:
            bin_7zz = self.utils_dir / "bin" / "7zz"
            if bin_7zz.exists():
                return str(bin_7zz)
            else:
                raise FileNotFoundError("7zz binary not found")