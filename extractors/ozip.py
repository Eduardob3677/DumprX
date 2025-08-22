import subprocess
from pathlib import Path

from extractors.base import BaseExtractor


class OzipExtractor(BaseExtractor):
    def __init__(self, utils_dir: Path):
        super().__init__(utils_dir)
        self.ozipdecrypt = utils_dir / "oppo_ozip_decrypt" / "ozipdecrypt.py"
    
    def can_extract(self, file_path: Path) -> bool:
        if file_path.suffix.lower() == '.ozip':
            return True
        
        try:
            with open(file_path, 'rb') as f:
                header = f.read(12)
                return header.replace(b'\\0', b'') == b'OPPOENCRYPT!'
        except Exception:
            return False
    
    def extract(self, file_path: Path, output_dir: Path) -> Path:
        self.console.info("Extracting Oppo/Realme ozip file")
        
        work_dir = output_dir / "ozip_work"
        work_dir.mkdir(exist_ok=True)
        
        target_file = work_dir / file_path.name
        self._copy_file(file_path, target_file)
        
        self.console.info("Decrypting ozip and creating zip...")
        
        cmd = [
            "uv", "run", "--with-requirements", 
            str(self.utils_dir / "oppo_decrypt" / "requirements.txt"),
            str(self.ozipdecrypt), str(target_file)
        ]
        
        result = subprocess.run(cmd, cwd=work_dir, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Ozip decryption failed: {result.stderr}")
        
        decrypted_zip = work_dir / f"{file_path.stem}.zip"
        if decrypted_zip.exists():
            from extractors.archive import ArchiveExtractor
            archive_extractor = ArchiveExtractor(self.utils_dir)
            return archive_extractor.extract(decrypted_zip, output_dir)
        
        out_dir = work_dir / "out"
        if out_dir.exists():
            return out_dir
        
        raise RuntimeError("Ozip extraction failed: no output found")