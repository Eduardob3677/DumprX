import os
import requests
from pathlib import Path
from urllib.parse import urlparse
from dumprx.core.config import Config
from dumprx.utils.console import console, ProgressManager

class DirectDownloader:
    def __init__(self, config: Config):
        self.config = config
    
    def download(self, url: str, output_dir: str) -> str:
        """Download directly from URL using requests or aria2c/wget"""
        
        if url.startswith('1drv.ms'):
            url = url.replace('1drv.ms', '1drv.ws')
        
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path) or "downloaded_file"
        output_path = os.path.join(output_dir, filename)
        
        try:
            return self._download_with_aria2c(url, output_dir)
        except Exception:
            try:
                return self._download_with_wget(url, output_dir)
            except Exception:
                return self._download_with_requests(url, output_path)
    
    def _download_with_aria2c(self, url: str, output_dir: str) -> str:
        """Download using aria2c"""
        import subprocess
        
        with ProgressManager() as progress:
            task = progress.add_task("Downloading with aria2c...", total=None)
            
            cmd = [
                'aria2c', '-x16', '-s8',
                '--console-log-level=warn',
                '--summary-interval=0',
                '--check-certificate=false',
                '--dir', output_dir,
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                downloaded_files = list(Path(output_dir).glob("*"))
                if downloaded_files:
                    return str(downloaded_files[-1])
            
            raise RuntimeError(f"aria2c failed: {result.stderr}")
    
    def _download_with_wget(self, url: str, output_dir: str) -> str:
        """Download using wget"""
        import subprocess
        
        with ProgressManager() as progress:
            task = progress.add_task("Downloading with wget...", total=None)
            
            cmd = [
                'wget', '-q', '--show-progress',
                '--progress=bar:force',
                '--no-check-certificate',
                '-P', output_dir,
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                downloaded_files = list(Path(output_dir).glob("*"))
                if downloaded_files:
                    return str(downloaded_files[-1])
            
            raise RuntimeError(f"wget failed: {result.stderr}")
    
    def _download_with_requests(self, url: str, output_path: str) -> str:
        """Download using Python requests"""
        chunk_size = self.config.get('download.chunk_size', 8192)
        timeout = self.config.get('download.timeout', 30)
        
        with ProgressManager() as progress:
            response = requests.get(url, stream=True, timeout=timeout)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            task = progress.add_task("Downloading...", total=total_size)
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        progress.update_task(task, advance=len(chunk))
        
        return output_path