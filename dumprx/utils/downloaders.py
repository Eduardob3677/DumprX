import os
import re
import subprocess
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from rich.console import Console
from rich.progress import Progress, DownloadColumn, BarColumn, TextColumn, TimeRemainingColumn

class DownloadManager:
    def __init__(self, config, console: Console):
        self.config = config
        self.console = console
    
    def download(self, url: str, download_dir: Path) -> Optional[Path]:
        url_lower = url.lower()
        
        if 'mega.nz' in url_lower or 'mega.co.nz' in url_lower:
            return self._download_mega(url, download_dir)
        elif 'mediafire.com' in url_lower:
            return self._download_mediafire(url, download_dir)
        elif 'drive.google.com' in url_lower:
            return self._download_google_drive(url, download_dir)
        elif 'androidfilehost.com' in url_lower:
            return self._download_afh(url, download_dir)
        elif '1drv.ms' in url_lower or 'onedrive.live.com' in url_lower:
            return self._download_onedrive(url, download_dir)
        else:
            return self._download_direct(url, download_dir)
    
    def _download_mega(self, url: str, download_dir: Path) -> Optional[Path]:
        try:
            self.console.print("[blue]📥 Downloading from Mega.nz...[/blue]")
            
            mega_script = self.config.utils_dir / "downloaders" / "mega-media-drive_dl.sh"
            if not mega_script.exists():
                self.console.print("[red]❌ Mega downloader script not found[/red]")
                return None
            
            os.chdir(download_dir)
            
            result = subprocess.run([
                'bash', str(mega_script), url
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                downloaded_files = list(download_dir.glob("*"))
                if downloaded_files:
                    return max(downloaded_files, key=lambda x: x.stat().st_mtime)
            
            self.console.print(f"[red]❌ Mega download failed: {result.stderr}[/red]")
            return None
            
        except Exception as e:
            self.console.print(f"[red]💥 Mega download error: {str(e)}[/red]")
            return None
    
    def _download_mediafire(self, url: str, download_dir: Path) -> Optional[Path]:
        try:
            self.console.print("[blue]📥 Downloading from MediaFire...[/blue]")
            
            result = subprocess.run([
                'curl', '-L', '-o', '-', url
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                return None
            
            download_match = re.search(r'href="(https://download\\d+\\.mediafire\\.com[^"]+)"', result.stdout)
            if download_match:
                download_url = download_match.group(1)
                filename_match = re.search(r'<span class="filename">([^<]+)</span>', result.stdout)
                filename = filename_match.group(1) if filename_match else 'mediafire_download'
                
                return self._download_with_aria2c(download_url, download_dir, filename)
            
            return None
            
        except Exception as e:
            self.console.print(f"[red]💥 MediaFire download error: {str(e)}[/red]")
            return None
    
    def _download_google_drive(self, url: str, download_dir: Path) -> Optional[Path]:
        try:
            self.console.print("[blue]📥 Downloading from Google Drive...[/blue]")
            
            file_id_match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', url)
            if not file_id_match:
                file_id_match = re.search(r'id=([a-zA-Z0-9_-]+)', url)
            
            if not file_id_match:
                self.console.print("[red]❌ Could not extract Google Drive file ID[/red]")
                return None
            
            file_id = file_id_match.group(1)
            download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            
            return self._download_with_aria2c(download_url, download_dir)
            
        except Exception as e:
            self.console.print(f"[red]💥 Google Drive download error: {str(e)}[/red]")
            return None
    
    def _download_afh(self, url: str, download_dir: Path) -> Optional[Path]:
        try:
            self.console.print("[blue]📥 Downloading from AndroidFileHost...[/blue]")
            
            afh_script = self.config.utils_dir / "downloaders" / "afh_dl.py"
            if not afh_script.exists():
                self.console.print("[red]❌ AFH downloader script not found[/red]")
                return None
            
            os.chdir(download_dir)
            
            result = subprocess.run([
                'python3', str(afh_script), url
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                downloaded_files = list(download_dir.glob("*"))
                if downloaded_files:
                    return max(downloaded_files, key=lambda x: x.stat().st_mtime)
            
            self.console.print(f"[red]❌ AFH download failed: {result.stderr}[/red]")
            return None
            
        except Exception as e:
            self.console.print(f"[red]💥 AFH download error: {str(e)}[/red]")
            return None
    
    def _download_onedrive(self, url: str, download_dir: Path) -> Optional[Path]:
        try:
            self.console.print("[blue]📥 Downloading from OneDrive...[/blue]")
            
            if '1drv.ms' in url:
                result = subprocess.run([
                    'curl', '-L', '--head', url
                ], capture_output=True, text=True)
                
                location_match = re.search(r'Location: (.+)', result.stdout)
                if location_match:
                    url = location_match.group(1).strip()
            
            download_url = url.replace('?e=', '&download=1?e=') if '?e=' in url else url + '&download=1'
            
            return self._download_with_aria2c(download_url, download_dir)
            
        except Exception as e:
            self.console.print(f"[red]💥 OneDrive download error: {str(e)}[/red]")
            return None
    
    def _download_direct(self, url: str, download_dir: Path) -> Optional[Path]:
        try:
            self.console.print("[blue]📥 Downloading from direct URL...[/blue]")
            
            parsed_url = urlparse(url)
            filename = Path(parsed_url.path).name
            if not filename or '.' not in filename:
                filename = 'download'
            
            return self._download_with_aria2c(url, download_dir, filename)
            
        except Exception as e:
            self.console.print(f"[red]💥 Direct download error: {str(e)}[/red]")
            return None
    
    def _download_with_aria2c(self, url: str, download_dir: Path, filename: str = None) -> Optional[Path]:
        try:
            download_dir.mkdir(parents=True, exist_ok=True)
            os.chdir(download_dir)
            
            cmd = [
                'aria2c',
                '--file-allocation=none',
                '--max-connection-per-server=10',
                '--max-concurrent-downloads=10',
                '--split=10',
                '--min-split-size=1M',
                '--continue=true',
                '--auto-file-renaming=false'
            ]
            
            if filename:
                cmd.extend(['--out', filename])
            
            cmd.append(url)
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                if filename:
                    downloaded_file = download_dir / filename
                    if downloaded_file.exists():
                        return downloaded_file
                
                downloaded_files = [f for f in download_dir.iterdir() if f.is_file()]
                if downloaded_files:
                    return max(downloaded_files, key=lambda x: x.stat().st_mtime)
            
            self.console.print(f"[red]❌ aria2c download failed: {result.stderr}[/red]")
            return None
            
        except Exception as e:
            self.console.print(f"[red]💥 aria2c download error: {str(e)}[/red]")
            return None