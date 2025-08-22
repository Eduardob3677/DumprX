import os
import subprocess
from pathlib import Path
from dumprx.core.config import Config
from dumprx.utils.console import console, ProgressManager

class GDriveDownloader:
    def __init__(self, config: Config):
        self.config = config
    
    def download(self, url: str, output_dir: str) -> str:
        """Download from Google Drive using external script"""
        script_path = Path(__file__).parent.parent.parent / "utils" / "downloaders" / "mega-media-drive_dl.sh"
        
        if not script_path.exists():
            raise FileNotFoundError(f"GDrive downloader script not found: {script_path}")
        
        original_cwd = os.getcwd()
        try:
            os.chdir(output_dir)
            
            with ProgressManager() as progress:
                task = progress.add_task("Downloading from Google Drive...", total=None)
                
                result = subprocess.run([str(script_path), url], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    downloaded_files = list(Path(output_dir).glob("*"))
                    if downloaded_files:
                        return str(downloaded_files[0])
                
                raise RuntimeError(f"Google Drive download failed: {result.stderr}")
        
        finally:
            os.chdir(original_cwd)