import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from downloaders.mega import MegaDownloader
from downloaders.afh import AfhDownloader
from downloaders.direct import DirectDownloader
from utils.console import Console


class DownloadManager:
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.console = Console()
        
        self.downloaders = {
            'mega.nz': MegaDownloader(),
            'mediafire.com': MegaDownloader(),
            'drive.google.com': MegaDownloader(),
            'androidfilehost.com': AfhDownloader(),
            'we.tl': DirectDownloader(),
            'default': DirectDownloader()
        }
    
    def download(self, url: str) -> str:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        os.chdir(self.output_dir)
        
        self._cleanup_directory()
        
        downloader = self._get_downloader(url)
        downloaded_file = downloader.download(url, self.output_dir)
        
        self._sanitize_filenames()
        
        return downloaded_file
    
    def _get_downloader(self, url: str):
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        for key, downloader in self.downloaders.items():
            if key in domain:
                return downloader
        
        return self.downloaders['default']
    
    def _cleanup_directory(self):
        for item in self.output_dir.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                import shutil
                shutil.rmtree(item)
    
    def _sanitize_filenames(self):
        for item in self.output_dir.iterdir():
            try:
                subprocess.run(['detox', '-r', str(item)], 
                             check=False, capture_output=True)
            except FileNotFoundError:
                pass