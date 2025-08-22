import os
import re
import asyncio
import aiohttp
import aiofiles
import subprocess
import urllib.parse
from pathlib import Path
from typing import Optional, Tuple, List
from abc import ABC, abstractmethod

from ..core.logger import Logger
from ..core.config import Config

class DownloadError(Exception):
    """Exception raised for download errors."""
    pass

class BaseDownloader(ABC):
    def __init__(self, logger: Logger, config: Config):
        self.logger = logger
        self.config = config
    
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        pass
    
    @abstractmethod
    async def download(self, url: str, output_dir: str) -> str:
        pass

class AsyncDirectDownloader(BaseDownloader):
    def can_handle(self, url: str) -> bool:
        return url.startswith(('http://', 'https://'))
    
    async def download(self, url: str, output_dir: str) -> str:
        if '1drv.ms' in url:
            url = url.replace('ms', 'ws')
        
        filename = self._extract_filename(url)
        output_path = Path(output_dir) / filename
        
        self.logger.download("Starting download", f"URL: {url}")
        
        try:
            return await self._download_with_aria2c(url, output_path)
        except Exception:
            self.logger.info("Aria2c failed, trying aiohttp")
            return await self._download_with_aiohttp(url, output_path)
    
    async def _download_with_aria2c(self, url: str, output_path: Path) -> str:
        process = await asyncio.create_subprocess_exec(
            "aria2c", 
            *self.config.downloads.aria2c_args.split(),
            "--out", output_path.name,
            "--dir", str(output_path.parent),
            url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), 
            timeout=self.config.downloads.timeout
        )
        
        if process.returncode == 0 and output_path.exists():
            self.logger.success("Download completed", f"File: {output_path.name}")
            return str(output_path)
        else:
            raise DownloadError(f"Aria2c failed: {stderr.decode()}")
    
    async def _download_with_aiohttp(self, url: str, output_path: Path) -> str:
        timeout = aiohttp.ClientTimeout(total=self.config.downloads.timeout)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise DownloadError(f"HTTP {response.status}: {response.reason}")
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                async with aiofiles.open(output_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(self.config.downloads.chunk_size):
                        await f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            self.logger.progress("Downloading", downloaded, total_size)
        
        self.logger.success("Download completed", f"File: {output_path.name}")
        return str(output_path)
    
    def _extract_filename(self, url: str) -> str:
        parsed = urllib.parse.urlparse(url)
        filename = os.path.basename(parsed.path)
        
        if not filename or '.' not in filename:
            filename = "firmware_download"
        
        return filename

class MegaMediaDriveDownloader(BaseDownloader):
    def can_handle(self, url: str) -> bool:
        supported_domains = ['mega.nz', 'mediafire.com', 'drive.google.com']
        return any(domain in url for domain in supported_domains)
    
    async def download(self, url: str, output_dir: str) -> str:
        script_path = self.config.get_tool_path('mega_media_drive_dl')
        if not script_path or not Path(script_path).exists():
            script_path = Path(self.config.get_utils_dir()) / "downloaders" / "mega-media-drive_dl.sh"
        
        if not Path(script_path).exists():
            raise DownloadError(f"Download script not found: {script_path}")
        
        self.logger.download("Downloading from cloud storage", f"Service: {self._get_service_name(url)}")
        
        process = await asyncio.create_subprocess_exec(
            "bash", str(script_path), url,
            cwd=output_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=self.config.downloads.timeout
        )
        
        if process.returncode != 0:
            raise DownloadError(f"Download failed: {stderr.decode()}")
        
        files = list(Path(output_dir).glob("*"))
        if not files:
            raise DownloadError("No files downloaded")
        
        downloaded_file = max(files, key=lambda f: f.stat().st_size)
        self.logger.success("Download completed", f"File: {downloaded_file.name}")
        
        return str(downloaded_file)
    
    def _get_service_name(self, url: str) -> str:
        if 'mega.nz' in url:
            return "Mega.nz"
        elif 'mediafire.com' in url:
            return "MediaFire" 
        elif 'drive.google.com' in url:
            return "Google Drive"
        return "Unknown"

class AndroidFileHostDownloader(BaseDownloader):
    def can_handle(self, url: str) -> bool:
        return 'androidfilehost.com' in url
    
    async def download(self, url: str, output_dir: str) -> str:
        script_path = Path(self.config.get_utils_dir()) / "downloaders" / "afh_dl.py"
        
        if not script_path.exists():
            raise DownloadError(f"AFH downloader not found: {script_path}")
        
        self.logger.download("Downloading from AndroidFileHost")
        
        process = await asyncio.create_subprocess_exec(
            "python3", str(script_path), "-l", url,
            cwd=output_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=self.config.downloads.timeout
        )
        
        if process.returncode != 0:
            raise DownloadError(f"AFH download failed: {stderr.decode()}")
        
        files = list(Path(output_dir).glob("*"))
        if not files:
            raise DownloadError("No files downloaded from AFH")
        
        downloaded_file = max(files, key=lambda f: f.stat().st_size)
        self.logger.success("Download completed", f"File: {downloaded_file.name}")
        
        return str(downloaded_file)

class TransferDownloader(BaseDownloader):
    def can_handle(self, url: str) -> bool:
        return '/we.tl/' in url
    
    async def download(self, url: str, output_dir: str) -> str:
        transfer_path = Path(self.config.get_utils_dir()) / "bin" / "transfer"
        
        if not transfer_path.exists():
            raise DownloadError(f"Transfer tool not found: {transfer_path}")
        
        self.logger.download("Downloading from WeTransfer")
        
        process = await asyncio.create_subprocess_exec(
            str(transfer_path), url,
            cwd=output_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=self.config.downloads.timeout
        )
        
        if process.returncode != 0:
            raise DownloadError(f"WeTransfer download failed: {stderr.decode()}")
        
        files = list(Path(output_dir).glob("*"))
        if not files:
            raise DownloadError("No files downloaded from WeTransfer")
        
        downloaded_file = max(files, key=lambda f: f.stat().st_size)
        self.logger.success("Download completed", f"File: {downloaded_file.name}")
        
        return str(downloaded_file)

class DownloadManager:
    def __init__(self, logger: Logger, config: Config):
        self.logger = logger
        self.config = config
        self.downloaders = [
            MegaMediaDriveDownloader(logger, config),
            AndroidFileHostDownloader(logger, config),
            TransferDownloader(logger, config),
            AsyncDirectDownloader(logger, config)
        ]
    
    async def download(self, url: str, output_dir: str) -> str:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        for file in Path(output_dir).glob("*"):
            if file.is_file():
                file.unlink()
        
        for downloader in self.downloaders:
            if downloader.can_handle(url):
                for attempt in range(self.config.downloads.max_retries):
                    try:
                        return await downloader.download(url, output_dir)
                    except DownloadError as e:
                        if attempt == self.config.downloads.max_retries - 1:
                            raise
                        self.logger.warning(f"Download attempt {attempt + 1} failed", str(e))
                        await asyncio.sleep(2 ** attempt)
        
        raise DownloadError(f"No downloader available for URL: {url}")
    
    def is_url(self, path: str) -> bool:
        return bool(re.match(r'^https?://.*$', path))
    
    def get_supported_services(self) -> List[str]:
        return [
            "Direct HTTP/HTTPS links",
            "Mega.nz",
            "MediaFire",
            "Google Drive", 
            "OneDrive (1drv.ms)",
            "AndroidFileHost",
            "WeTransfer"
        ]