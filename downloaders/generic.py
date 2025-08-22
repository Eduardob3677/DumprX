import subprocess
import requests
from urllib.parse import urlparse
from rich.console import Console
from rich.progress import Progress, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn

console = Console()

class GenericDownloader:
    def __init__(self):
        self.session = requests.Session()
    
    def download_with_requests(self, url, filename=None):
        if not filename:
            parsed = urlparse(url)
            filename = parsed.path.split('/')[-1] or 'download'
        
        with Progress(
            "[progress.description]{task.description}",
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            task = progress.add_task(f"Downloading {filename}", total=total_size)
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        progress.update(task, advance=len(chunk))
            
            return filename
    
    def download_with_aria2c(self, url):
        try:
            result = subprocess.run([
                'aria2c', '-x16', '-s8', '--console-log-level=warn',
                '--summary-interval=0', '--check-certificate=false', url
            ], check=True, capture_output=True, text=True)
            return ["downloaded_file"]
        except subprocess.CalledProcessError as e:
            raise Exception(f"aria2c failed: {e}")
        except FileNotFoundError:
            raise Exception("aria2c not found")
    
    def download_with_wget(self, url):
        try:
            result = subprocess.run([
                'wget', '-q', '--show-progress', '--progress=bar:force',
                '--no-check-certificate', url
            ], check=True, capture_output=True, text=True)
            return ["downloaded_file"]
        except subprocess.CalledProcessError as e:
            raise Exception(f"wget failed: {e}")
        except FileNotFoundError:
            raise Exception("wget not found")
    
    def download(self, url):
        console.print("Generic Download Link Detected")
        
        if 'onedrive' in url or '1drv.ms' in url:
            url = url.replace('1drv.ms', '1drv.ws')
        
        try:
            return self.download_with_aria2c(url)
        except Exception as e1:
            console.print(f"[yellow]aria2c failed: {e1}[/yellow]")
            try:
                return self.download_with_wget(url)
            except Exception as e2:
                console.print(f"[yellow]wget failed: {e2}[/yellow]")
                console.print("Falling back to Python requests...")
                filename = self.download_with_requests(url)
                return [filename]