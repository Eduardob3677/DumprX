import os
import re
import json
import base64
import subprocess
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
from dumprx.utils.logging import logger

class DownloadManager:
    def __init__(self, config):
        self.config = config
        
    def download(self, url: str) -> Optional[str]:
        if 'mega' in url:
            return self._download_mega(url)
        elif 'mediafire' in url:
            return self._download_mediafire(url)
        elif 'drive.google.com' in url:
            return self._download_gdrive(url)
        elif 'androidfilehost.com' in url:
            return self._download_afh(url)
        elif url.startswith(('http://', 'https://')):
            return self._download_direct(url)
        else:
            logger.error(f"Unsupported URL: {url}")
            return None
    
    def _download_mega(self, url: str) -> Optional[str]:
        logger.info("Mega.NZ Website Link Detected")
        
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.backends import default_backend
            import struct
        except ImportError:
            logger.error("Cryptography library required for Mega downloads")
            return None
            
        link_vars = self._parse_mega_url(url)
        if not link_vars:
            return None
            
        file_id = link_vars.get('id')
        key = link_vars.get('key')
        
        if not file_id or not key:
            logger.error("Invalid Mega URL format")
            return None
            
        try:
            key_bytes = self._url_decode(key)
            key_decoded = base64.b64decode(key_bytes + '==')
            
            api_url = f"https://g.api.mega.co.nz/cs?id=&n={file_id}"
            
            response = requests.post(api_url, json=[{"a": "g", "p": file_id}])
            if response.status_code != 200:
                logger.error("Failed to get Mega file info")
                return None
                
            data = response.json()
            if not data or 'g' not in data[0]:
                logger.error("Invalid Mega API response")
                return None
                
            download_url = data[0]['g']
            attrs = data[0].get('at', '')
            
            if attrs:
                attrs_decoded = self._decrypt_mega_attrs(attrs, key_decoded)
                filename = attrs_decoded.get('n', 'unknown_file')
            else:
                filename = f"mega_file_{file_id}"
                
            return self._download_with_decrypt(download_url, filename, key_decoded)
            
        except Exception as e:
            logger.error(f"Mega download failed: {e}")
            return None
    
    def _parse_mega_url(self, url: str) -> Dict[str, str]:
        if '#F!' in url:
            parts = url.split('#F!')[-1].split('!')
            return {'type': 'folder', 'id': parts[0], 'key': parts[1] if len(parts) > 1 else None}
        elif '#!' in url:
            parts = url.split('#!')[-1].split('!')
            return {'type': 'file', 'id': parts[0], 'key': parts[1] if len(parts) > 1 else None}
        else:
            return {}
    
    def _url_decode(self, data: str) -> str:
        return data.replace('-', '+').replace('_', '/').replace(',', '')
    
    def _decrypt_mega_attrs(self, attrs: str, key: bytes) -> Dict[str, str]:
        try:
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            attrs_bytes = base64.b64decode(self._url_decode(attrs) + '==')
            
            cipher = Cipher(algorithms.AES(key[:16]), modes.CBC(b'\x00' * 16), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted = decryptor.update(attrs_bytes) + decryptor.finalize()
            
            attrs_json = decrypted.rstrip(b'\x00').decode('utf-8')
            return json.loads(attrs_json)
        except Exception:
            return {}
    
    def _download_with_decrypt(self, url: str, filename: str, key: bytes) -> Optional[str]:
        output_path = self.config.input_dir / filename
        
        try:
            logger.info(f"Downloading file {filename}...")
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.success(f"Downloaded: {filename}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None
    
    def _download_mediafire(self, url: str) -> Optional[str]:
        logger.info("Mediafire Website Link Detected")
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            download_url_match = re.search(r'href="(https://download[^"]+)"', response.text)
            if not download_url_match:
                logger.error("Could not find Mediafire download URL")
                return None
                
            download_url = download_url_match.group(1)
            
            filename_match = re.search(r'([^/]+)$', download_url)
            filename = filename_match.group(1) if filename_match else 'mediafire_download'
            
            return self._download_direct(download_url, filename)
            
        except Exception as e:
            logger.error(f"Mediafire download failed: {e}")
            return None
    
    def _download_gdrive(self, url: str) -> Optional[str]:
        logger.info("Google Drive URL detected")
        
        try:
            file_id_match = re.search(r'([0-9a-zA-Z_-]{33})', url)
            if not file_id_match:
                logger.error("Could not extract Google Drive file ID")
                return None
                
            file_id = file_id_match.group(1)
            
            download_url = f"https://docs.google.com/uc?export=download&id={file_id}"
            
            session = requests.Session()
            response = session.get(download_url)
            
            if 'confirm=' in response.text:
                confirm_match = re.search(r'confirm=([0-9A-Za-z_]+)', response.text)
                if confirm_match:
                    confirm_token = confirm_match.group(1)
                    download_url = f"https://docs.google.com/uc?export=download&confirm={confirm_token}&id={file_id}"
                    
            filename = f"gdrive_file_{file_id}"
            return self._download_direct(download_url, filename, session=session)
            
        except Exception as e:
            logger.error(f"Google Drive download failed: {e}")
            return None
    
    def _download_afh(self, url: str) -> Optional[str]:
        logger.info("AndroidFileHost URL detected")
        
        try:
            afhdl_script = self.config.python_tools['afhdl']
            result = subprocess.run(['python3', str(afhdl_script), url], 
                                  capture_output=True, text=True, cwd=self.config.input_dir)
            
            if result.returncode == 0:
                downloaded_files = list(self.config.input_dir.glob('*'))
                if downloaded_files:
                    return str(downloaded_files[-1])
                    
            logger.error("AFH download failed")
            return None
            
        except Exception as e:
            logger.error(f"AFH download failed: {e}")
            return None
    
    def _download_direct(self, url: str, filename: Optional[str] = None, session: Optional[requests.Session] = None) -> Optional[str]:
        if not filename:
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path) or 'downloaded_file'
            
        output_path = self.config.input_dir / filename
        
        try:
            logger.info(f"Downloading {filename}...")
            
            if session:
                response = session.get(url, stream=True)
            else:
                response = requests.get(url, stream=True)
                
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as f:
                if total_size > 0:
                    from rich.progress import Progress, BarColumn, TextColumn, FileSizeColumn, TransferSpeedColumn
                    
                    with Progress(
                        TextColumn("[progress.description]{task.description}"),
                        BarColumn(),
                        FileSizeColumn(),
                        TransferSpeedColumn(),
                    ) as progress:
                        task = progress.add_task(f"Downloading {filename}", total=total_size)
                        
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                progress.update(task, advance=len(chunk))
                else:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            
            logger.success(f"Downloaded: {filename}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return None