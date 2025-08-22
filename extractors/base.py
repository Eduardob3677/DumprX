import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from utils.console import Console


class BaseExtractor(ABC):
    def __init__(self, utils_dir: Path):
        self.utils_dir = Path(utils_dir)
        self.console = Console()
    
    @abstractmethod
    def can_extract(self, file_path: Path) -> bool:
        pass
    
    @abstractmethod
    def extract(self, file_path: Path, output_dir: Path) -> Path:
        pass
    
    def _copy_file(self, src: Path, dst: Path):
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    
    def _run_command(self, cmd: list, cwd: Path = None, check: bool = True) -> subprocess.CompletedProcess:
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            capture_output=True, 
            text=True,
            check=False
        )
        
        if check and result.returncode != 0:
            raise RuntimeError(f"Command failed: {' '.join(cmd)}\\nError: {result.stderr}")
        
        return result