import subprocess
from pathlib import Path

from extractors.base import BaseExtractor


class ArchiveExtractor(BaseExtractor):
    def __init__(self, utils_dir: Path):
        super().__init__(utils_dir)
        self.seven_zip = self._find_7zip()
    
    def _find_7zip(self):
        try:
            subprocess.run(['7zz', '--help'], capture_output=True, check=True)
            return '7zz'
        except (subprocess.CalledProcessError, FileNotFoundError):
            return str(self.utils_dir / "bin" / "7zz")
    
    def can_extract(self, file_path: Path) -> bool:
        extensions = ['.zip', '.rar', '.7z', '.tar', '.tar.gz', '.tgz']
        return file_path.suffix.lower() in extensions
    
    def extract(self, file_path: Path, output_dir: Path) -> Path:
        self.console.info(f"Extracting archive: {file_path.name}")
        
        extract_dir = output_dir / f"{file_path.stem}_extracted"
        extract_dir.mkdir(exist_ok=True)
        
        cmd = [self.seven_zip, 'x', '-y', str(file_path), f'-o{extract_dir}']
        result = self._run_command(cmd)
        
        if result.returncode != 0:
            raise RuntimeError(f"Archive extraction failed: {result.stderr}")
        
        return extract_dir


class SuperImageExtractor(BaseExtractor):
    def can_extract(self, file_path: Path) -> bool:
        return 'super' in file_path.name.lower() and '.img' in file_path.name.lower()
    
    def extract(self, file_path: Path, output_dir: Path) -> Path:
        self.console.info("Extracting super image partitions")
        
        work_dir = output_dir / "super_work"
        work_dir.mkdir(exist_ok=True)
        
        super_img = work_dir / "super.img"
        self._copy_file(file_path, super_img)
        
        lpunpack = self.utils_dir / "lpunpack"
        simg2img = self.utils_dir / "bin" / "simg2img"
        
        os.chdir(work_dir)
        
        if simg2img.exists():
            cmd = [str(simg2img), str(super_img), "super.img.raw"]
            self._run_command(cmd, check=False)
            
            if Path("super.img.raw").exists():
                super_img = Path("super.img.raw")
        
        partitions = [
            "system", "system_ext", "vendor", "product", "odm", 
            "system_dlkm", "vendor_dlkm", "odm_dlkm"
        ]
        
        for partition in partitions:
            for suffix in ["_a", ""]:
                partition_name = f"{partition}{suffix}"
                cmd = [str(lpunpack), f"--partition={partition_name}", str(super_img)]
                result = self._run_command(cmd, check=False)
                
                if result.returncode == 0:
                    img_file = Path(f"{partition_name}.img")
                    if img_file.exists() and suffix == "_a":
                        img_file.rename(f"{partition}.img")
        
        return work_dir


class PayloadExtractor(BaseExtractor):
    def can_extract(self, file_path: Path) -> bool:
        return file_path.name.lower() == 'payload.bin'
    
    def extract(self, file_path: Path, output_dir: Path) -> Path:
        self.console.info("Extracting OTA payload")
        
        work_dir = output_dir / "payload_work"
        work_dir.mkdir(exist_ok=True)
        
        payload_extractor = self.utils_dir / "bin" / "payload-dumper-go"
        
        cmd = [str(payload_extractor), str(file_path)]
        result = self._run_command(cmd, cwd=work_dir)
        
        if result.returncode != 0:
            raise RuntimeError(f"Payload extraction failed: {result.stderr}")
        
        return work_dir