"""
Mega.nz downloader implementation.

Provides download functionality for Mega.nz links.
"""

import re
import json
import base64
import struct
from pathlib import Path
from typing import Union, Optional, Dict, Any
from urllib.parse import urlparse, parse_qs

from dumprxbase import BaseDownloader, DownloadResult
from dumprxutils.console import print_info, print_error, print_warning


class MegaDownloader(BaseDownloader):
    """Downloader for Mega.nz files and folders."""
    
    def __init__(self):
        super().__init__()
        self.api_url = "https://g.api.mega.co.nz/cs"
    
    def download(self, url: str, output_dir: Union[str, Path]) -> DownloadResult:
        """
        Download file from Mega.nz URL.
        
        Args:
            url: Mega.nz URL
            output_dir: Directory to save file to
            
        Returns:
            DownloadResult with operation status
        """
        output_path = Path(output_dir)
        
        try:
            # Parse Mega URL
            link_info = self._parse_mega_url(url)
            if not link_info:
                return DownloadResult(success=False, error="Invalid Mega.nz URL")
            
            print_info(f"Processing Mega.nz link: {link_info['type']}")
            
            if link_info['type'] == 'file':
                return self._download_file_link(link_info, output_path)
            elif link_info['type'] == 'folder':
                return self._download_folder_link(link_info, output_path)
            else:
                return DownloadResult(success=False, error="Unsupported Mega.nz link type")
                
        except Exception as e:
            error_msg = f"Mega.nz download failed: {e}"
            print_error(error_msg)
            return DownloadResult(success=False, error=error_msg)
    
    def _parse_mega_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Parse Mega.nz URL to extract file/folder information."""
        # Mega.nz URL patterns:
        # File: https://mega.nz/file/ID#KEY or https://mega.nz/#!ID!KEY
        # Folder: https://mega.nz/folder/ID#KEY or https://mega.nz/#F!ID!KEY
        
        # Modern format
        if '/file/' in url:
            match = re.search(r'/file/([^#]+)#(.+)', url)
            if match:
                return {
                    'type': 'file',
                    'id': match.group(1),
                    'key': match.group(2)
                }
        
        elif '/folder/' in url:
            match = re.search(r'/folder/([^#]+)#(.+)', url)
            if match:
                return {
                    'type': 'folder',
                    'id': match.group(1),
                    'key': match.group(2)
                }
        
        # Legacy format
        elif '/#!' in url:
            match = re.search(r'/#!([^!]+)!(.+)', url)
            if match:
                return {
                    'type': 'file',
                    'id': match.group(1),
                    'key': match.group(2)
                }
        
        elif '/#F!' in url:
            match = re.search(r'/#F!([^!]+)!(.+)', url)
            if match:
                return {
                    'type': 'folder',
                    'id': match.group(1),
                    'key': match.group(2)
                }
        
        return None
    
    def _download_file_link(self, link_info: Dict, output_dir: Path) -> DownloadResult:
        """Download single file from Mega.nz."""
        try:
            # Get file information
            file_info = self._get_file_info(link_info['id'])
            if not file_info:
                return DownloadResult(success=False, error="Could not get file information")
            
            # Decrypt filename
            filename = self._decrypt_filename(file_info['attributes'], link_info['key'])
            if not filename:
                filename = f"mega_download_{link_info['id']}"
            
            # Get download URL
            download_url = self._get_download_url(link_info['id'])
            if not download_url:
                return DownloadResult(success=False, error="Could not get download URL")
            
            # Resolve file path
            filepath = self._resolve_filename(download_url, output_dir, filename)
            
            # Download file
            return self._download_file(download_url, filepath, file_info.get('size'))
            
        except Exception as e:
            return DownloadResult(success=False, error=f"File download failed: {e}")
    
    def _download_folder_link(self, link_info: Dict, output_dir: Path) -> DownloadResult:
        """Download folder from Mega.nz."""
        print_warning("Mega.nz folder downloads not fully implemented yet")
        return DownloadResult(success=False, error="Folder downloads not yet supported")
    
    def _get_file_info(self, file_id: str) -> Optional[Dict]:
        """Get file information from Mega API."""
        try:
            # Prepare API request
            request_data = [{"a": "g", "p": file_id}]
            
            response = self.session.post(
                self.api_url,
                json=request_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    return data[0]
            
            return None
            
        except Exception:
            return None
    
    def _get_download_url(self, file_id: str) -> Optional[str]:
        """Get direct download URL from Mega API."""
        try:
            # Request download URL
            request_data = [{"a": "g", "g": 1, "p": file_id}]
            
            response = self.session.post(
                self.api_url,
                json=request_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    return data[0].get('g')
            
            return None
            
        except Exception:
            return None
    
    def _decrypt_filename(self, attributes: str, key: str) -> Optional[str]:
        """Decrypt filename from Mega attributes."""
        try:
            # This is a simplified version - full Mega decryption is complex
            # For now, we'll try to extract any readable filename
            
            # Decode base64 attributes
            attr_data = base64.b64decode(attributes + '==')
            
            # Look for filename in attributes (simplified)
            attr_str = attr_data.decode('utf-8', errors='ignore')
            
            # Try to extract JSON and get filename
            if '{' in attr_str:
                json_start = attr_str.find('{')
                json_end = attr_str.rfind('}') + 1
                json_str = attr_str[json_start:json_end]
                
                try:
                    attr_json = json.loads(json_str)
                    if 'n' in attr_json:
                        return attr_json['n']
                except:
                    pass
            
            return None
            
        except Exception:
            return None