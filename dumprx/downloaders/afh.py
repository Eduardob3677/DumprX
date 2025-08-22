import os
import subprocess
import sys
from pathlib import Path
from dumprx.core.config import Config
from dumprx.utils.console import console, ProgressManager

class AFHDownloader:
    def __init__(self, config: Config):
        self.config = config
    
    def download(self, url: str, output_dir: str) -> str:
        """Download from AndroidFileHost using Python script"""
        script_path = Path(__file__).parent.parent.parent / "utils" / "downloaders" / "afh_dl.py"
        
        if not script_path.exists():
            raise FileNotFoundError(f"AFH downloader script not found: {script_path}")
        
        original_cwd = os.getcwd()
        try:
            os.chdir(output_dir)
            
            with ProgressManager() as progress:
                task = progress.add_task("Downloading from AndroidFileHost...", total=None)
                
                result = subprocess.run([sys.executable, str(script_path), "-l", url], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    downloaded_files = list(Path(output_dir).glob("*"))
                    if downloaded_files:
                        return str(downloaded_files[0])
                
                raise RuntimeError(f"AndroidFileHost download failed: {result.stderr}")
        
        finally:
            os.chdir(original_cwd)