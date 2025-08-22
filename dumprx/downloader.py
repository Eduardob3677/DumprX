#!/usr/bin/env python3

import os
import re
import json
import base64
import binascii
import subprocess
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests
from Crypto.Cipher import AES
from rich.console import Console
from rich.progress import Progress, DownloadColumn, BarColumn, TextColumn, TimeRemainingColumn

console = Console()

class FirmwareDownloader:
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def download_from_url(self, url: str) -> Optional[Path]:
        parsed_url = urlparse(url.lower())
        domain = parsed_url.netloc
        
        if 'mega.nz' in domain or 'mega.co.nz' in domain:
            return self._download_mega(url)
        elif 'mediafire.com' in domain:
            return self._download_mediafire(url)
        elif 'drive.google.com' in domain:
            return self._download_gdrive(url)
        elif 'androidfilehost.com' in domain:
            return self._download_afh(url)
        else:
            return self._download_direct(url)
    
    def _download_direct(self, url: str) -> Optional[Path]:
        console.print(f"[blue]Direct download from: {url}[/blue]")
        
        try:
            response = requests.head(url, allow_redirects=True)
            filename = self._get_filename_from_response(response, url)
            output_path = self.output_dir / filename
            
            # Download with progress bar
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                
                with Progress(
                    TextColumn("[bold blue]{task.description}"),
                    BarColumn(),
                    DownloadColumn(),
                    TimeRemainingColumn(),
                    console=console
                ) as progress:
                    download_task = progress.add_task(f"Downloading {filename}", total=total_size)
                    
                    with open(output_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                            progress.update(download_task, advance=len(chunk))
            
            console.print(f"[green]Downloaded: {output_path}[/green]")
            return output_path
            
        except Exception as e:
            console.print(f"[red]Download failed: {e}[/red]")
            return None
    
    def _download_mega(self, url: str) -> Optional[Path]:
        console.print("[blue]Mega.nz link detected[/blue]")
        console.print("[yellow]Note: For Mega.nz downloads, consider using megadl tool separately[/yellow]")
        
        try:
            # Try using megadl if available
            if subprocess.run(['which', 'megadl'], capture_output=True).returncode == 0:
                cmd = ['megadl', '--path', str(self.output_dir), url]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    # Find downloaded file
                    for file in self.output_dir.iterdir():
                        if file.is_file() and file.stat().st_size > 1024:  # > 1KB
                            return file
                else:
                    console.print(f"[red]megadl failed: {result.stderr}[/red]")
            else:
                console.print("[yellow]megadl not found. Install with: pip install mega.py[/yellow]")
                
        except Exception as e:
            console.print(f"[red]Mega download failed: {e}[/red]")
        
        return None
    
    def _download_mediafire(self, url: str) -> Optional[Path]:
        console.print("[blue]MediaFire link detected[/blue]")
        
        try:
            # Get the actual download URL
            response = requests.get(url)
            response.raise_for_status()
            
            # Extract download URL from page
            download_pattern = r'href="(http[s]?://download\d+\.mediafire\.com/[^"]+)"'
            match = re.search(download_pattern, response.text)
            
            if match:
                download_url = match.group(1)
                return self._download_direct(download_url)
            else:
                console.print("[red]Could not extract download URL from MediaFire page[/red]")
                
        except Exception as e:
            console.print(f"[red]MediaFire download failed: {e}[/red]")
        
        return None
    
    def _download_gdrive(self, url: str) -> Optional[Path]:
        console.print("[blue]Google Drive link detected[/blue]")
        
        try:
            # Extract file ID from URL
            file_id_pattern = r'(?:id=|d/|file/d/)([0-9a-zA-Z_-]{28,})'
            match = re.search(file_id_pattern, url)
            
            if not match:
                console.print("[red]Could not extract file ID from Google Drive URL[/red]")
                return None
            
            file_id = match.group(1)
            
            # Try to get download confirmation token
            session = requests.Session()
            response = session.get(f"https://docs.google.com/uc?export=download&id={file_id}")
            
            # Look for confirmation token
            confirm_pattern = r'name="confirm" value="([^"]+)"'
            confirm_match = re.search(confirm_pattern, response.text)
            
            if confirm_match:
                confirm_token = confirm_match.group(1)
                download_url = f"https://docs.google.com/uc?export=download&confirm={confirm_token}&id={file_id}"
            else:
                download_url = f"https://docs.google.com/uc?export=download&id={file_id}"
            
            return self._download_direct(download_url)
            
        except Exception as e:
            console.print(f"[red]Google Drive download failed: {e}[/red]")
        
        return None
    
    def _download_afh(self, url: str) -> Optional[Path]:
        console.print("[blue]AndroidFileHost link detected[/blue]")
        
        try:
            # Extract file ID
            fid_pattern = r'fid=(\d+)'
            match = re.search(fid_pattern, url)
            
            if not match:
                console.print("[red]Could not extract file ID from AFH URL[/red]")
                return None
            
            file_id = match.group(1)
            
            # Get download mirrors
            mirrors = self._get_afh_mirrors(file_id)
            if not mirrors:
                console.print("[red]Could not get download mirrors from AFH[/red]")
                return None
            
            # Use first available mirror
            mirror_url = mirrors[0]['url']
            return self._download_direct(mirror_url)
            
        except Exception as e:
            console.print(f"[red]AndroidFileHost download failed: {e}[/red]")
        
        return None
    
    def _get_afh_mirrors(self, file_id: str) -> Optional[list]:
        try:
            # Get cookies first
            session = requests.Session()
            session.get(f"https://androidfilehost.com/?fid={file_id}")
            
            # Get mirrors
            mirror_url = "https://androidfilehost.com/libs/otf/mirrors.otf.php"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Referer": f"https://androidfilehost.com/?fid={file_id}",
                "X-Requested-With": "XMLHttpRequest"
            }
            
            post_data = {
                "submit": "submit",
                "action": "getdownloadmirrors",
                "fid": file_id
            }
            
            response = session.post(mirror_url, headers=headers, data=post_data)
            mirror_data = response.json()
            
            if mirror_data.get("STATUS") == "1" and mirror_data.get("CODE") == "200":
                return mirror_data.get("MIRRORS", [])
            
        except Exception as e:
            console.print(f"[red]Error getting AFH mirrors: {e}[/red]")
        
        return None
    
    def _get_filename_from_response(self, response, url: str) -> str:
        # Try to get filename from Content-Disposition header
        content_disposition = response.headers.get('content-disposition')
        if content_disposition:
            filename_match = re.search(r'filename[*]?=(?:["\']?)([^"\';\n]+)', content_disposition)
            if filename_match:
                return filename_match.group(1).strip('"\'')
        
        # Fallback to URL
        parsed_url = urlparse(url)
        filename = Path(parsed_url.path).name
        
        if not filename or filename == '/':
            filename = "firmware_download"
        
        return filename