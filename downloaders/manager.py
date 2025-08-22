import os
import re
import subprocess
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from downloaders.mega import MegaDownloader
from downloaders.mediafire import MediaFireDownloader
from downloaders.gdrive import GDriveDownloader
from downloaders.afh import AFHDownloader
from downloaders.wetransfer import WeTransferDownloader
from downloaders.generic import GenericDownloader

console = Console()

class DownloadManager:
    def __init__(self, output_dir="input"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.downloaders = {
            'mega': MegaDownloader(),
            'mediafire': MediaFireDownloader(),
            'gdrive': GDriveDownloader(),
            'afh': AFHDownloader(),
            'wetransfer': WeTransferDownloader(),
            'generic': GenericDownloader(),
        }
    
    def detect_downloader(self, url):
        if 'mega.nz' in url:
            return 'mega'
        elif 'mediafire.com' in url:
            return 'mediafire'
        elif 'drive.google.com' in url:
            return 'gdrive'
        elif 'androidfilehost.com' in url:
            return 'afh'
        elif 'we.tl' in url or 'wetransfer.com' in url:
            return 'wetransfer'
        else:
            return 'generic'
    
    def download(self, url):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Detecting download type...", total=None)
            
            downloader_type = self.detect_downloader(url)
            downloader = self.downloaders[downloader_type]
            
            progress.update(task, description=f"Downloading with {downloader_type} downloader...")
            
            try:
                old_cwd = os.getcwd()
                os.chdir(self.output_dir)
                
                downloaded_files = downloader.download(url)
                
                self._detox_filenames()
                
                progress.update(task, description="Download completed")
                return downloaded_files
                
            finally:
                os.chdir(old_cwd)
    
    def _detox_filenames(self):
        try:
            subprocess.run(['detox', '-r', '.'], check=False, capture_output=True)
        except FileNotFoundError:
            pass