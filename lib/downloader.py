import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse
import subprocess
import shutil
from .ui import UI
from .config import config

class Downloader:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.user_agents = config.get('download.user_agents', {})
        self.chunk_size = config.get('download.chunk_size', 8192)
        self.timeout = config.get('download.timeout', 300)
        self.retry_attempts = config.get('download.retry_attempts', 3)
        self.retry_delay = config.get('download.retry_delay', 5)
    
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def is_supported_url(self, url: str) -> bool:
        supported_hosts = config.get('urls.supported_hosts', [])
        parsed = urlparse(url)
        return any(host in parsed.netloc for host in supported_hosts)
    
    async def download(self, url: str, output_dir: str) -> Optional[Path]:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if self._is_mega_url(url):
            return await self._download_mega(url, output_path)
        elif self._is_mediafire_url(url):
            return await self._download_mediafire(url, output_path)
        elif self._is_gdrive_url(url):
            return await self._download_gdrive(url, output_path)
        elif self._is_afh_url(url):
            return await self._download_afh(url, output_path)
        elif self._is_wetransfer_url(url):
            return await self._download_wetransfer(url, output_path)
        else:
            return await self._download_direct(url, output_path)
    
    def _is_mega_url(self, url: str) -> bool:
        return "mega.nz" in url
    
    def _is_mediafire_url(self, url: str) -> bool:
        return "mediafire.com" in url
    
    def _is_gdrive_url(self, url: str) -> bool:
        return "drive.google.com" in url
    
    def _is_afh_url(self, url: str) -> bool:
        return "androidfilehost.com" in url
    
    def _is_wetransfer_url(self, url: str) -> bool:
        return "/we.tl/" in url
    
    async def _download_mega(self, url: str, output_path: Path) -> Optional[Path]:
        UI.processing("Downloading from MEGA...")
        script_path = Path("utils/downloaders/mega-media-drive_dl.sh")
        if not script_path.exists():
            UI.error("MEGA downloader script not found")
            return None
        
        try:
            process = await asyncio.create_subprocess_exec(
                str(script_path), url,
                cwd=str(output_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            files = list(output_path.glob("*"))
            return files[0] if files else None
        except Exception as e:
            UI.error(f"MEGA download failed: {e}")
            return None
    
    async def _download_afh(self, url: str, output_path: Path) -> Optional[Path]:
        UI.processing("Downloading from AndroidFileHost...")
        script_path = Path("utils/downloaders/afh_dl.py")
        if not script_path.exists():
            UI.error("AFH downloader script not found")
            return None
        
        try:
            process = await asyncio.create_subprocess_exec(
                "python3", str(script_path), "-l", url,
                cwd=str(output_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            files = list(output_path.glob("*"))
            return files[0] if files else None
        except Exception as e:
            UI.error(f"AFH download failed: {e}")
            return None
    
    async def _download_wetransfer(self, url: str, output_path: Path) -> Optional[Path]:
        UI.processing("Downloading from WeTransfer...")
        transfer_bin = Path("utils/bin/transfer")
        if not transfer_bin.exists():
            UI.error("Transfer binary not found")
            return None
        
        try:
            process = await asyncio.create_subprocess_exec(
                str(transfer_bin), url,
                cwd=str(output_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            files = list(output_path.glob("*"))
            return files[0] if files else None
        except Exception as e:
            UI.error(f"WeTransfer download failed: {e}")
            return None
    
    async def _download_mediafire(self, url: str, output_path: Path) -> Optional[Path]:
        return await self._download_with_script(url, output_path, "MediaFire")
    
    async def _download_gdrive(self, url: str, output_path: Path) -> Optional[Path]:
        return await self._download_with_script(url, output_path, "Google Drive")
    
    async def _download_with_script(self, url: str, output_path: Path, service: str) -> Optional[Path]:
        UI.processing(f"Downloading from {service}...")
        script_path = Path("utils/downloaders/mega-media-drive_dl.sh")
        
        try:
            process = await asyncio.create_subprocess_exec(
                str(script_path), url,
                cwd=str(output_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            files = list(output_path.glob("*"))
            return files[0] if files else None
        except Exception as e:
            UI.error(f"{service} download failed: {e}")
            return None
    
    async def _download_direct(self, url: str, output_path: Path) -> Optional[Path]:
        UI.processing("Downloading file...")
        
        if url.startswith("1drv.ms"):
            url = url.replace("ms", "ws")
        
        if shutil.which("aria2c"):
            return await self._download_with_aria2(url, output_path)
        else:
            return await self._download_with_wget(url, output_path)
    
    async def _download_with_aria2(self, url: str, output_path: Path) -> Optional[Path]:
        try:
            process = await asyncio.create_subprocess_exec(
                "aria2c", "-x16", "-s8", "--console-log-level=warn",
                "--summary-interval=0", "--check-certificate=false", url,
                cwd=str(output_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            files = list(output_path.glob("*"))
            return files[0] if files else None
        except Exception as e:
            UI.warning(f"aria2c failed, falling back to wget: {e}")
            return await self._download_with_wget(url, output_path)
    
    async def _download_with_wget(self, url: str, output_path: Path) -> Optional[Path]:
        try:
            process = await asyncio.create_subprocess_exec(
                "wget", "-q", "--show-progress", "--progress=bar:force",
                "--no-check-certificate", url,
                cwd=str(output_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            files = list(output_path.glob("*"))
            return files[0] if files else None
        except Exception as e:
            UI.error(f"wget download failed: {e}")
            return None