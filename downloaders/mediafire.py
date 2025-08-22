import re
import requests
from rich.console import Console
from rich.progress import Progress, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn

console = Console()

class MediaFireDownloader:
    def __init__(self):
        self.session = requests.Session()
    
    def get_direct_link(self, url):
        response = self.session.get(url)
        response.raise_for_status()
        
        pattern = r'href="([^"]*)" class="[^"]*btn[^"]*" id="downloadButton"'
        match = re.search(pattern, response.text)
        
        if match:
            return match.group(1)
        else:
            pattern = r'href="(http://download[^"]*\.mediafire\.com/[^"]*)"'
            match = re.search(pattern, response.text)
            if match:
                return match.group(1)
        
        raise Exception("Could not find MediaFire download link")
    
    def download_file(self, url, filename):
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
    
    def download(self, url):
        console.print("MediaFire Website Link Detected")
        
        try:
            direct_url = self.get_direct_link(url)
            
            filename = direct_url.split('/')[-1].split('?')[0]
            if not filename or '.' not in filename:
                filename = "mediafire_download"
            
            self.download_file(direct_url, filename)
            return [filename]
            
        except Exception as e:
            console.print(f"[red]MediaFire download failed: {e}[/red]")
            console.print("Falling back to aria2c...")
            
            import subprocess
            try:
                result = subprocess.run([
                    'aria2c', '-c', '-s16', '-x16', '-m10', 
                    '--console-log-level=warn', '--summary-interval=0',
                    '--check-certificate=false', url
                ], check=True, capture_output=True, text=True)
                return ["downloaded_file"]
            except subprocess.CalledProcessError as e:
                raise Exception(f"aria2c failed: {e}")
            except FileNotFoundError:
                raise Exception("aria2c not found and MediaFire direct download failed")