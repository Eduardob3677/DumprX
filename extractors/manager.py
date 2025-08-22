import os
import shutil
import subprocess
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class ExtractorManager:
    def __init__(self, config):
        self.config = config
        self.bin_dir = Path(__file__).parent.parent / "bin"
        
        self.extractors = {
            '.zip': self._extract_zip,
            '.rar': self._extract_rar,
            '.7z': self._extract_7z,
            '.tar': self._extract_tar,
            '.tar.gz': self._extract_tar,
            '.tgz': self._extract_tar,
            '.tar.md5': self._extract_tar,
            '.ozip': self._extract_ozip,
            '.ofp': self._extract_ofp,
            '.ops': self._extract_ops,
            '.kdz': self._extract_kdz,
            '.nb0': self._extract_nb0,
            '.pac': self._extract_pac,
            '.bin': self._extract_bin,
            '.img': self._extract_img,
            '.sin': self._extract_sin,
        }
    
    def detect_format(self, filepath):
        path = Path(filepath)
        
        if path.name.lower().startswith('ruu_') and path.suffix.lower() == '.exe':
            return 'ruu'
        elif path.name.upper() == 'UPDATE.APP':
            return 'update_app'
        elif 'payload.bin' in path.name.lower():
            return 'payload'
        elif 'super' in path.name.lower() and path.suffix.lower() == '.img':
            return 'super'
        elif path.suffix.lower() in ['.new.dat', '.new.dat.br', '.new.dat.xz']:
            return 'sdat'
        elif path.name.lower().endswith('.emmc.img'):
            return 'emmc'
        elif path.name.lower().endswith('.img.ext4'):
            return 'ext4_img'
        elif 'chunk' in path.name.lower():
            return 'chunk'
        else:
            for ext, extractor in self.extractors.items():
                if str(path).lower().endswith(ext.lower()):
                    return ext
        
        return 'unknown'
    
    def extract(self, filepath, output_dir):
        format_type = self.detect_format(filepath)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Extracting {format_type} format...", total=None)
            
            if format_type in self.extractors:
                return self.extractors[format_type](filepath, output_dir)
            elif hasattr(self, f'_extract_{format_type}'):
                extractor = getattr(self, f'_extract_{format_type}')
                return extractor(filepath, output_dir)
            else:
                raise Exception(f"Unsupported format: {format_type}")
    
    def _run_command(self, cmd, cwd=None):
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Command failed: {cmd}\nError: {result.stderr}")
        return result.stdout
    
    def _extract_zip(self, filepath, output_dir):
        cmd = f'7zz x "{filepath}" -o"{output_dir}"'
        self._run_command(cmd)
        return [output_dir]
    
    def _extract_rar(self, filepath, output_dir):
        cmd = f'7zz x "{filepath}" -o"{output_dir}"'
        self._run_command(cmd)
        return [output_dir]
    
    def _extract_7z(self, filepath, output_dir):
        cmd = f'7zz x "{filepath}" -o"{output_dir}"'
        self._run_command(cmd)
        return [output_dir]
    
    def _extract_tar(self, filepath, output_dir):
        cmd = f'tar -xf "{filepath}" -C "{output_dir}"'
        self._run_command(cmd)
        return [output_dir]
    
    def _extract_ozip(self, filepath, output_dir):
        from extractors.ozip import OzipExtractor
        extractor = OzipExtractor(self.config)
        return extractor.extract(filepath, output_dir)
    
    def _extract_ofp(self, filepath, output_dir):
        from extractors.ofp import OfpExtractor
        extractor = OfpExtractor(self.config)
        return extractor.extract(filepath, output_dir)
    
    def _extract_ops(self, filepath, output_dir):
        from extractors.ops import OpsExtractor
        extractor = OpsExtractor(self.config)
        return extractor.extract(filepath, output_dir)
    
    def _extract_kdz(self, filepath, output_dir):
        from extractors.kdz import KdzExtractor
        extractor = KdzExtractor(self.config)
        return extractor.extract(filepath, output_dir)
    
    def _extract_nb0(self, filepath, output_dir):
        cmd = f'{self.bin_dir}/nb0-extract "{filepath}" "{output_dir}"'
        self._run_command(cmd)
        return [output_dir]
    
    def _extract_pac(self, filepath, output_dir):
        from extractors.pac import PacExtractor
        extractor = PacExtractor(self.config)
        return extractor.extract(filepath, output_dir)
    
    def _extract_update_app(self, filepath, output_dir):
        from extractors.update_app import UpdateAppExtractor
        extractor = UpdateAppExtractor(self.config)
        return extractor.extract(filepath, output_dir)
    
    def _extract_payload(self, filepath, output_dir):
        cmd = f'{self.bin_dir}/payload-dumper-go -o "{output_dir}" "{filepath}"'
        self._run_command(cmd)
        return [output_dir]
    
    def _extract_super(self, filepath, output_dir):
        cmd = f'{self.bin_dir}/lpunpack "{filepath}" "{output_dir}"'
        self._run_command(cmd)
        return [output_dir]
    
    def _extract_sdat(self, filepath, output_dir):
        from extractors.sdat import SdatExtractor
        extractor = SdatExtractor(self.config)
        return extractor.extract(filepath, output_dir)
    
    def _extract_ruu(self, filepath, output_dir):
        cmd = f'{self.bin_dir}/RUU_Decrypt_Tool -s "{filepath}"'
        self._run_command(cmd, cwd=output_dir)
        return [output_dir]