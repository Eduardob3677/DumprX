import subprocess
from pathlib import Path

from downloaders.base import BaseDownloader


class MegaDownloader(BaseDownloader):
    def download(self, url: str, output_dir: Path) -> str:
        script_path = Path("bin/downloaders/mega-media-drive_dl.sh")
        
        if not script_path.exists():
            raise RuntimeError("Mega downloader script not found")
        
        cmd = [str(script_path), url]
        result = subprocess.run(cmd, cwd=output_dir, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Mega download failed: {result.stderr}")
        
        downloaded_files = list(output_dir.glob("*"))
        if not downloaded_files:
            raise RuntimeError("No files downloaded")
        
        return str(downloaded_files[0])