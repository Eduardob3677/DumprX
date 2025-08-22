"""
Base downloader class and common utilities for all downloaders.
"""

import requests
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union
from dataclasses import dataclass

from ..utils.console import print_info, print_error, ProgressContext
from ..modules.formatter import format_file_size, sanitize_filename


@dataclass
class DownloadResult:
    """Result of download operation."""
    success: bool
    filepath: Optional[Path] = None
    size: int = 0
    error: Optional[str] = None


class BaseDownloader(ABC):
    """Base class for all downloaders."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DumprX/2.0.0 (Python)'
        })
    
    @abstractmethod
    def download(self, url: str, output_dir: Union[str, Path]) -> DownloadResult:
        """
        Download file from URL.
        
        Args:
            url: URL to download from
            output_dir: Directory to save file to
            
        Returns:
            DownloadResult with operation status
        """
        pass
    
    def _download_file(self, url: str, filepath: Path, 
                      expected_size: Optional[int] = None) -> DownloadResult:
        """
        Common file download implementation.
        
        Args:
            url: Direct download URL
            filepath: Local file path to save to
            expected_size: Expected file size for progress tracking
            
        Returns:
            DownloadResult with operation status
        """
        try:
            print_info(f"Downloading: {filepath.name}")
            
            # Ensure output directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Start download with streaming
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            # Get file size from headers if not provided
            if expected_size is None:
                try:
                    expected_size = int(response.headers.get('content-length', 0))
                except:
                    expected_size = 0
            
            downloaded_size = 0
            
            with open(filepath, 'wb') as f:
                with ProgressContext(f"Downloading {filepath.name}") as progress:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)
                            
                            if expected_size > 0:
                                progress.update(downloaded_size, expected_size)
            
            print_info(f"Downloaded: {format_file_size(downloaded_size)}")
            
            return DownloadResult(
                success=True,
                filepath=filepath,
                size=downloaded_size
            )
            
        except Exception as e:
            error_msg = f"Download failed: {e}"
            print_error(error_msg)
            
            # Clean up partial download
            if filepath.exists():
                try:
                    filepath.unlink()
                except:
                    pass
            
            return DownloadResult(success=False, error=error_msg)
    
    def _get_filename_from_url(self, url: str) -> str:
        """Extract filename from URL."""
        from urllib.parse import urlparse, unquote
        
        parsed = urlparse(url)
        filename = Path(unquote(parsed.path)).name
        
        if not filename or filename == '/':
            filename = "download"
        
        return sanitize_filename(filename)
    
    def _get_filename_from_headers(self, response: requests.Response) -> Optional[str]:
        """Extract filename from Content-Disposition header."""
        import re
        
        content_disposition = response.headers.get('content-disposition')
        if content_disposition:
            # Look for filename parameter
            match = re.search(r'filename[*]?=([^;]+)', content_disposition)
            if match:
                filename = match.group(1).strip().strip('"\'')
                return sanitize_filename(filename)
        
        return None
    
    def _resolve_filename(self, url: str, output_dir: Path, 
                         suggested_name: Optional[str] = None) -> Path:
        """
        Resolve final filename for download.
        
        Args:
            url: Download URL
            output_dir: Output directory
            suggested_name: Suggested filename
            
        Returns:
            Full file path
        """
        if suggested_name:
            filename = sanitize_filename(suggested_name)
        else:
            filename = self._get_filename_from_url(url)
        
        # Ensure we have a filename
        if not filename:
            filename = "firmware_download"
        
        filepath = output_dir / filename
        
        # Handle filename conflicts
        counter = 1
        original_filepath = filepath
        while filepath.exists():
            stem = original_filepath.stem
            suffix = original_filepath.suffix
            filepath = output_dir / f"{stem}_{counter}{suffix}"
            counter += 1
        
        return filepath