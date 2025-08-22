import os
import subprocess
import requests
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from rich.progress import Progress, DownloadColumn, BarColumn, TransferSpeedColumn
import re

class DownloaderManager:
    def __init__(self, console, verbose=False):
        self.console = console
        self.verbose = verbose
        
    def download(self, url, output_dir):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if self._is_mega_url(url):
            return self._download_mega(url, output_dir)
        elif self._is_mediafire_url(url):
            return self._download_mediafire(url, output_dir)
        elif self._is_gdrive_url(url):
            return self._download_gdrive(url, output_dir)
        elif self._is_afh_url(url):
            return self._download_afh(url, output_dir)
        else:
            return self._download_direct(url, output_dir)
    
    def _is_mega_url(self, url):
        return 'mega.nz' in url or 'mega.co.nz' in url
    
    def _is_mediafire_url(self, url):
        return 'mediafire.com' in url or 'download.mediafire.com' in url
    
    def _is_gdrive_url(self, url):
        return 'drive.google.com' in url or 'docs.google.com' in url
    
    def _is_afh_url(self, url):
        return 'androidfilehost.com' in url
    
    def _download_mega(self, url, output_dir):
        self.console.print("[blue]📥 Downloading from MEGA...[/blue]")
        try:
            utils_dir = Path(__file__).parent.parent.parent / "utils"
            mega_script = utils_dir / "downloaders" / "mega-media-drive_dl.sh"
            
            if mega_script.exists():
                result = subprocess.run([
                    "bash", str(mega_script), url
                ], cwd=output_dir, capture_output=True, text=True)
                
                if result.returncode == 0:
                    downloaded_files = list(output_dir.glob("*"))
                    if downloaded_files:
                        return downloaded_files[0]
                else:
                    self.console.print(f"[red]❌ MEGA download failed: {result.stderr}[/red]")
            
            return self._download_with_aria2c(url, output_dir)
            
        except Exception as e:
            if self.verbose:
                self.console.print(f"[yellow]⚠️  MEGA download error: {str(e)}[/yellow]")
            return self._download_direct(url, output_dir)
    
    def _download_mediafire(self, url, output_dir):
        self.console.print("[blue]📥 Downloading from MediaFire...[/blue]")
        try:
            utils_dir = Path(__file__).parent.parent.parent / "utils"
            mediafire_script = utils_dir / "downloaders" / "mega-media-drive_dl.sh"
            
            if mediafire_script.exists():
                result = subprocess.run([
                    "bash", str(mediafire_script), url
                ], cwd=output_dir, capture_output=True, text=True)
                
                if result.returncode == 0:
                    downloaded_files = list(output_dir.glob("*"))
                    if downloaded_files:
                        return downloaded_files[0]
            
            return self._download_with_aria2c(url, output_dir)
            
        except Exception as e:
            if self.verbose:
                self.console.print(f"[yellow]⚠️  MediaFire download error: {str(e)}[/yellow]")
            return self._download_direct(url, output_dir)
    
    def _download_gdrive(self, url, output_dir):
        self.console.print("[blue]📥 Downloading from Google Drive...[/blue]")
        try:
            utils_dir = Path(__file__).parent.parent.parent / "utils"
            gdrive_script = utils_dir / "downloaders" / "mega-media-drive_dl.sh"
            
            if gdrive_script.exists():
                result = subprocess.run([
                    "bash", str(gdrive_script), url
                ], cwd=output_dir, capture_output=True, text=True)
                
                if result.returncode == 0:
                    downloaded_files = list(output_dir.glob("*"))
                    if downloaded_files:
                        return downloaded_files[0]
            
            return self._download_with_aria2c(url, output_dir)
            
        except Exception as e:
            if self.verbose:
                self.console.print(f"[yellow]⚠️  Google Drive download error: {str(e)}[/yellow]")
            return self._download_direct(url, output_dir)
    
    def _download_afh(self, url, output_dir):
        self.console.print("[blue]📥 Downloading from AndroidFileHost...[/blue]")
        try:
            utils_dir = Path(__file__).parent.parent.parent / "utils"
            afh_script = utils_dir / "downloaders" / "afh_dl.py"
            
            if afh_script.exists():
                result = subprocess.run([
                    "python3", str(afh_script), "-l", url
                ], cwd=output_dir, capture_output=True, text=True)
                
                if result.returncode == 0:
                    downloaded_files = list(output_dir.glob("*"))
                    if downloaded_files:
                        return downloaded_files[0]
                else:
                    self.console.print(f"[red]❌ AFH download failed: {result.stderr}[/red]")
            
            return self._download_direct(url, output_dir)
            
        except Exception as e:
            if self.verbose:
                self.console.print(f"[yellow]⚠️  AndroidFileHost download error: {str(e)}[/yellow]")
            return self._download_direct(url, output_dir)
    
    def _download_with_aria2c(self, url, output_dir):
        try:
            result = subprocess.run([
                "aria2c", "-x", "16", "-s", "16", url, "-d", str(output_dir)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                downloaded_files = list(output_dir.glob("*"))
                if downloaded_files:
                    return downloaded_files[0]
            
        except FileNotFoundError:
            pass
        
        return self._download_direct(url, output_dir)
    
    def _download_direct(self, url, output_dir):
        self.console.print("[blue]📥 Direct download...[/blue]")
        try:
            response = requests.head(url, allow_redirects=True)
            filename = self._extract_filename(url, response.headers)
            
            filepath = output_dir / filename
            
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                
                with Progress(
                    DownloadColumn(),
                    BarColumn(),
                    TransferSpeedColumn(),
                    console=self.console
                ) as progress:
                    task = progress.add_task(f"📥 {filename}", total=total_size)
                    
                    with open(filepath, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                progress.update(task, advance=len(chunk))
            
            return filepath
            
        except Exception as e:
            self.console.print(f"[red]❌ Direct download failed: {str(e)}[/red]")
            return None
    
    def _extract_filename(self, url, headers):
        content_disposition = headers.get('content-disposition')
        if content_disposition:
            filename_match = re.search(r'filename="?([^"]+)"?', content_disposition)
            if filename_match:
                return filename_match.group(1)
        
        parsed_url = urlparse(url)
        filename = Path(parsed_url.path).name
        
        if not filename or '.' not in filename:
            filename = f"firmware_{hash(url) % 10000}.bin"
        
        return filename