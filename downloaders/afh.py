import subprocess
from pathlib import Path

from downloaders.base import BaseDownloader


class AfhDownloader(BaseDownloader):
    def download(self, url: str, output_dir: Path) -> str:
        script_path = Path("bin/downloaders/afh_dl.py")
        
        if not script_path.exists():
            raise RuntimeError("AFH downloader script not found")
        
        cmd = ["python3", str(script_path), "-l", url]
        result = subprocess.run(cmd, cwd=output_dir, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"AFH download failed: {result.stderr}")
        
        downloaded_files = list(output_dir.glob("*"))
        if not downloaded_files:
            raise RuntimeError("No files downloaded")
        
        return str(downloaded_files[0])


class DirectDownloader(BaseDownloader):
    def download(self, url: str, output_dir: Path) -> str:
        if "1drv.ms" in url:
            url = url.replace("ms", "ws")
        
        try:
            cmd = [
                "aria2c", "-x16", "-s8", "--console-log-level=warn", 
                "--summary-interval=0", "--check-certificate=false", url
            ]
            result = subprocess.run(cmd, cwd=output_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                downloaded_files = list(output_dir.glob("*"))
                if downloaded_files:
                    return str(downloaded_files[0])
        except FileNotFoundError:
            pass
        
        try:
            cmd = [
                "wget", "-q", "--show-progress", "--progress=bar:force", 
                "--no-check-certificate", url
            ]
            result = subprocess.run(cmd, cwd=output_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                downloaded_files = list(output_dir.glob("*"))
                if downloaded_files:
                    return str(downloaded_files[0])
        except FileNotFoundError:
            pass
        
        raise RuntimeError("No download tool available (aria2c or wget)")