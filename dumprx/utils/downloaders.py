import re
import requests
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from rich.console import Console
from rich.progress import Progress, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn


class FileDownloader:
    def __init__(self, console: Console):
        self.console = console
    
    def download(self, url: str, output_dir: Path) -> Optional[Path]:
        if "mega.nz" in url or "mega.co.nz" in url:
            return self._download_mega(url, output_dir)
        elif "mediafire.com" in url:
            return self._download_mediafire(url, output_dir)
        elif "androidfilehost.com" in url:
            return self._download_afh(url, output_dir)
        elif "drive.google.com" in url:
            return self._download_gdrive(url, output_dir)
        else:
            return self._download_direct(url, output_dir)
    
    def _download_direct(self, url: str, output_dir: Path) -> Optional[Path]:
        try:
            response = requests.head(url, allow_redirects=True)
            content_disposition = response.headers.get('content-disposition')
            
            if content_disposition:
                filename = re.findall('filename="(.+)"', content_disposition)
                filename = filename[0] if filename else Path(urlparse(url).path).name
            else:
                filename = Path(urlparse(url).path).name
            
            if not filename:
                filename = "downloaded_file"
            
            output_path = output_dir / filename
            
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                
                with Progress(
                    "[progress.description]{task.description}",
                    "[progress.percentage]{task.percentage:>3.0f}%",
                    DownloadColumn(),
                    TransferSpeedColumn(),
                    TimeRemainingColumn(),
                    console=self.console
                ) as progress:
                    task = progress.add_task(f"Downloading {filename}", total=total_size)
                    
                    with open(output_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                progress.advance(task, len(chunk))
            
            return output_path
            
        except Exception as e:
            self.console.print(f"[red]Failed to download {url}: {e}[/red]")
            return None
    
    def _download_mega(self, url: str, output_dir: Path) -> Optional[Path]:
        self.console.print("[yellow]Mega.nz downloads require the mega-media-drive_dl.sh script[/yellow]")
        return None
    
    def _download_mediafire(self, url: str, output_dir: Path) -> Optional[Path]:
        self.console.print("[yellow]MediaFire downloads require the mega-media-drive_dl.sh script[/yellow]")
        return None
    
    def _download_afh(self, url: str, output_dir: Path) -> Optional[Path]:
        self.console.print("[yellow]AndroidFileHost downloads require the afh_dl.py script[/yellow]")
        return None
    
    def _download_gdrive(self, url: str, output_dir: Path) -> Optional[Path]:
        self.console.print("[yellow]Google Drive downloads not implemented yet[/yellow]")
        return None