"""
MediaFire downloader implementation.
"""

import re
from pathlib import Path
from typing import Union
from urllib.parse import unquote

from .base import BaseDownloader, DownloadResult
from ..utils.console import print_info, print_error


class MediaFireDownloader(BaseDownloader):
    """Downloader for MediaFire files."""
    
    def download(self, url: str, output_dir: Union[str, Path]) -> DownloadResult:
        """
        Download file from MediaFire URL.
        
        Args:
            url: MediaFire URL
            output_dir: Directory to save file to
            
        Returns:
            DownloadResult with operation status
        """
        output_path = Path(output_dir)
        
        try:
            print_info("Processing MediaFire link...")
            
            # Get the MediaFire page
            response = self.session.get(url)
            response.raise_for_status()
            
            page_content = response.text
            
            # Extract direct download link
            download_url = self._extract_download_url(page_content)
            if not download_url:
                return DownloadResult(success=False, error="Could not find download link")
            
            # Extract filename
            filename = self._extract_filename(page_content, download_url)
            
            # Resolve file path
            filepath = self._resolve_filename(download_url, output_path, filename)
            
            # Download file
            return self._download_file(download_url, filepath)
            
        except Exception as e:
            error_msg = f"MediaFire download failed: {e}"
            print_error(error_msg)
            return DownloadResult(success=False, error=error_msg)
    
    def _extract_download_url(self, page_content: str) -> str:
        """Extract direct download URL from MediaFire page."""
        # Look for download link in the page
        patterns = [
            r'href="(https?://download\d*\.mediafire\.com/[^"]+)"',
            r'href="(https?://[^"]*mediafire[^"]*\.com/[^"]*)"',
            r'"(https?://download[^"]*)"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, page_content)
            if match:
                url = match.group(1)
                # Make sure it's a download URL
                if 'download' in url:
                    return url
        
        return None
    
    def _extract_filename(self, page_content: str, download_url: str) -> str:
        """Extract filename from MediaFire page or URL."""
        # Try to find filename in page content
        filename_patterns = [
            r'<div[^>]*class="[^"]*filename[^"]*"[^>]*>([^<]+)</div>',
            r'<span[^>]*class="[^"]*filename[^"]*"[^>]*>([^<]+)</span>',
            r'<title>([^<]+) - MediaFire</title>',
            r'data-filename="([^"]+)"',
        ]
        
        for pattern in filename_patterns:
            match = re.search(pattern, page_content, re.IGNORECASE)
            if match:
                filename = match.group(1).strip()
                if filename and not filename.lower().startswith('mediafire'):
                    return filename
        
        # Fallback to extracting from URL
        filename = self._get_filename_from_url(download_url)
        if filename and filename != 'download':
            return filename
        
        return "mediafire_download"