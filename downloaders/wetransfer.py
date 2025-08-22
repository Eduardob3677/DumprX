import subprocess
from rich.console import Console

console = Console()

class WeTransferDownloader:
    def download(self, url):
        console.print("WeTransfer Website Link Detected")
        
        try:
            result = subprocess.run([
                'transfer', url
            ], check=True, capture_output=True, text=True, cwd='.')
            return ["transferred_file"]
        except subprocess.CalledProcessError as e:
            raise Exception(f"transfer command failed: {e}")
        except FileNotFoundError:
            raise Exception("transfer command not found in bin directory")