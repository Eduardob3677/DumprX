import asyncio
import aiohttp
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from typing import Optional
from ..ui import UI

class MegaDownloader:
    async def download(self, url: str, output_dir: Path) -> Optional[Path]:
        UI.processing("Downloading from MEGA...")
        
        try:
            import mega
            m = mega.Mega()
            m = m.login()
            
            if '#!' in url:
                file_id = url.split('#!')[-1]
                if '!' in file_id:
                    file_id = file_id.split('!')[0]
                
                file_info = m.get_public_file_info(url)
                filename = file_info['name']
                
                output_path = output_dir / filename
                m.download_url(url, str(output_dir))
                
                return output_path
            
        except ImportError:
            UI.warning("mega.py not installed, falling back to external tools")
            return await self._download_with_megadl(url, output_dir)
        except Exception as e:
            UI.warning(f"MEGA download failed with mega.py: {e}")
            return await self._download_with_megadl(url, output_dir)
    
    async def _download_with_megadl(self, url: str, output_dir: Path) -> Optional[Path]:
        try:
            process = await asyncio.create_subprocess_exec(
                "megadl", url,
                cwd=str(output_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            if process.returncode == 0:
                files = list(output_dir.glob("*"))
                return files[-1] if files else None
            
        except FileNotFoundError:
            UI.error("megadl not found and mega.py not available")
        
        return None

class MediaFireDownloader:
    async def download(self, url: str, output_dir: Path) -> Optional[Path]:
        UI.processing("Downloading from MediaFire...")
        
        try:
            direct_url = await self._get_direct_url(url)
            if not direct_url:
                return None
            
            async with aiohttp.ClientSession() as session:
                async with session.get(direct_url) as response:
                    if response.status == 200:
                        filename = self._get_filename_from_response(response)
                        if not filename:
                            filename = "mediafire_download"
                        
                        output_path = output_dir / filename
                        
                        with open(output_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                        
                        return output_path
            
        except Exception as e:
            UI.error(f"MediaFire download failed: {e}")
        
        return None
    
    async def _get_direct_url(self, url: str) -> Optional[str]:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    match = re.search(r'href="(https://download\d+\.mediafire\.com/[^"]+)"', content)
                    if match:
                        return match.group(1)
        
        return None
    
    def _get_filename_from_response(self, response) -> Optional[str]:
        content_disposition = response.headers.get('content-disposition', '')
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[-1].strip('"')
            return filename
        
        return None

class GoogleDriveDownloader:
    async def download(self, url: str, output_dir: Path) -> Optional[Path]:
        UI.processing("Downloading from Google Drive...")
        
        try:
            file_id = self._extract_file_id(url)
            if not file_id:
                UI.error("Could not extract Google Drive file ID")
                return None
            
            direct_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(direct_url, allow_redirects=False) as response:
                    if response.status in [302, 301]:
                        direct_url = response.headers.get('location', direct_url)
                
                async with session.get(direct_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        if 'virus scan warning' in content.lower():
                            confirm_url = self._extract_confirm_url(content, file_id)
                            if confirm_url:
                                async with session.get(confirm_url) as confirm_response:
                                    if confirm_response.status == 200:
                                        content = await confirm_response.read()
                                    else:
                                        return None
                            else:
                                return None
                        else:
                            content = await response.read()
                        
                        filename = self._get_filename_from_response(response) or f"gdrive_{file_id}"
                        output_path = output_dir / filename
                        
                        with open(output_path, 'wb') as f:
                            f.write(content)
                        
                        return output_path
            
        except Exception as e:
            UI.error(f"Google Drive download failed: {e}")
        
        return None
    
    def _extract_file_id(self, url: str) -> Optional[str]:
        patterns = [
            r'/file/d/([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)',
            r'/view\?usp=sharing',
            r'[&?]id=([a-zA-Z0-9-_]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_confirm_url(self, content: str, file_id: str) -> Optional[str]:
        match = re.search(r'href="(/uc\?export=download[^"]+)"', content)
        if match:
            return f"https://drive.google.com{match.group(1)}"
        
        return f"https://drive.google.com/uc?export=download&confirm=t&id={file_id}"
    
    def _get_filename_from_response(self, response) -> Optional[str]:
        content_disposition = response.headers.get('content-disposition', '')
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[-1].strip('"')
            return filename
        
        return None