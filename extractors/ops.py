import subprocess
from pathlib import Path

from extractors.base import BaseExtractor


class OpsExtractor(BaseExtractor):
    def __init__(self, utils_dir: Path):
        super().__init__(utils_dir)
        self.opsdecrypt = utils_dir / "oppo_decrypt" / "opscrypto.py"
    
    def can_extract(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.ops'
    
    def extract(self, file_path: Path, output_dir: Path) -> Path:
        self.console.info("Extracting Oppo/OnePlus ops file")
        
        work_dir = output_dir / "ops_work"
        work_dir.mkdir(exist_ok=True)
        
        target_file = work_dir / file_path.name
        self._copy_file(file_path, target_file)
        
        cmd = [
            "uv", "run", "--with-requirements",
            str(self.utils_dir / "oppo_decrypt" / "requirements.txt"),
            str(self.opsdecrypt), "decrypt", str(target_file)
        ]
        
        result = self._run_command(cmd, cwd=work_dir)
        
        if result.returncode != 0:
            raise RuntimeError(f"Ops decryption failed: {result.stderr}")
        
        extract_dir = work_dir / "extract"
        if extract_dir.exists():
            return extract_dir
        
        raise RuntimeError("Ops extraction failed: no output found")


class KdzExtractor(BaseExtractor):
    def __init__(self, utils_dir: Path):
        super().__init__(utils_dir)
        self.kdz_extract = utils_dir / "kdztools" / "unkdz.py"
        self.dz_extract = utils_dir / "kdztools" / "undz.py"
    
    def can_extract(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == '.kdz'
    
    def extract(self, file_path: Path, output_dir: Path) -> Path:
        self.console.info("Extracting LG KDZ file")
        
        work_dir = output_dir / "kdz_work"
        work_dir.mkdir(exist_ok=True)
        
        target_file = work_dir / file_path.name
        self._copy_file(file_path, target_file)
        
        os.chdir(work_dir)
        
        cmd = ["python3", str(self.kdz_extract), "-f", file_path.name, "-x", "-o", "./"]
        result = self._run_command(cmd, cwd=work_dir, check=False)
        
        dz_files = list(work_dir.glob("*.dz"))
        if dz_files:
            self.console.info("Extracting all partitions as individual images")
            for dz_file in dz_files:
                cmd = ["python3", str(self.dz_extract), "-f", str(dz_file), "-s", "-o", "./"]
                self._run_command(cmd, cwd=work_dir, check=False)
        
        return work_dir