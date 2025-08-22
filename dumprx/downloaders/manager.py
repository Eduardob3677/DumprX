import os
import re
import subprocess
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from dumprx.core.config import Config
from dumprx.utils.console import console, error, success, info
from dumprx.downloaders.mega import MegaDownloader
from dumprx.downloaders.mediafire import MediaFireDownloader
from dumprx.downloaders.gdrive import GDriveDownloader
from dumprx.downloaders.afh import AFHDownloader
from dumprx.downloaders.direct import DirectDownloader

class DownloadManager:
    def __init__(self, config: Config):
        self.config = config
        self.downloaders = {
            'mega': MegaDownloader(config),
            'mediafire': MediaFireDownloader(config),
            'gdrive': GDriveDownloader(config),
            'afh': AFHDownloader(config),
            'direct': DirectDownloader(config)
        }
    
    def download(self, url: str, output_dir: str = None) -> str:
        """Download file from URL and return local path"""
        if not output_dir:
            output_dir = self.config.get('input_dir', 'input')
        
        os.makedirs(output_dir, exist_ok=True)
        
        downloader = self._get_downloader(url)
        if not downloader:
            error(f"No suitable downloader found for URL: {url}")
            raise ValueError(f"Unsupported URL: {url}")
        
        info(f"Using {downloader.__class__.__name__} for download")
        local_path = downloader.download(url, output_dir)
        
        if local_path and os.path.exists(local_path):
            success(f"Downloaded to: {local_path}")
            self._sanitize_filename(local_path)
            return local_path
        else:
            error("Download failed")
            raise RuntimeError("Download failed")
    
    def _get_downloader(self, url: str):
        """Determine appropriate downloader for URL"""
        url_lower = url.lower()
        
        if 'mega.nz' in url_lower:
            return self.downloaders['mega']
        elif 'mediafire.com' in url_lower:
            return self.downloaders['mediafire']
        elif 'drive.google.com' in url_lower or 'googleapis.com' in url_lower:
            return self.downloaders['gdrive']
        elif 'androidfilehost.com' in url_lower:
            return self.downloaders['afh']
        elif url_lower.startswith(('http://', 'https://', 'ftp://')):
            return self.downloaders['direct']
        
        return None
    
    def _sanitize_filename(self, filepath: str) -> str:
        """Sanitize downloaded filename"""
        try:
            result = subprocess.run(['detox', '-r', filepath], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                info("Filename sanitized")
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        return filepath