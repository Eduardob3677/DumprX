import re
import subprocess
import requests
from rich.console import Console

console = Console()

class GDriveDownloader:
    def __init__(self):
        self.session = requests.Session()
    
    def extract_file_id(self, url):
        patterns = [
            r'/file/d/([a-zA-Z0-9_-]{25,})',
            r'id=([a-zA-Z0-9_-]{25,})',
            r'/open\?id=([a-zA-Z0-9_-]{25,})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise Exception("Could not extract Google Drive file ID from URL")
    
    def download(self, url):
        console.print("Google Drive Website Link Detected")
        
        try:
            file_id = self.extract_file_id(url)
            
            confirm_url = f"https://docs.google.com/uc?export=download&id={file_id}"
            response = self.session.get(confirm_url)
            
            confirm_token = None
            for line in response.text.split('\n'):
                if 'confirm=' in line:
                    match = re.search(r'confirm=([0-9A-Za-z_]+)', line)
                    if match:
                        confirm_token = match.group(1)
                        break
            
            if confirm_token:
                download_url = f"https://docs.google.com/uc?export=download&confirm={confirm_token}&id={file_id}"
            else:
                download_url = confirm_url
            
            try:
                result = subprocess.run([
                    'aria2c', '-c', '-s16', '-x16', '-m10',
                    '--console-log-level=warn', '--summary-interval=0',
                    '--check-certificate=false', '--load-cookies=/tmp/cookies.txt',
                    download_url
                ], check=True, capture_output=True, text=True)
                return ["downloaded_file"]
            except subprocess.CalledProcessError as e:
                raise Exception(f"aria2c failed: {e}")
            except FileNotFoundError:
                raise Exception("aria2c not found")
                
        except Exception as e:
            console.print(f"[red]Google Drive download failed: {e}[/red]")
            raise