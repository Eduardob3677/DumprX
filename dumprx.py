#!/usr/bin/env python3

import asyncio
import argparse
import sys
from pathlib import Path
import shutil
import yaml
from typing import Dict, Any, Optional

from lib.ui import UI
from lib.config import config
from lib.downloader import Downloader
from lib.extractors import FirmwareExtractor
from lib.git_manager import GitManager, TelegramNotifier
from lib.progress import create_progress_bar

class DumprX:
    def __init__(self):
        self.project_dir = Path(__file__).parent.absolute()
        self.input_dir = self.project_dir / "input"
        self.output_dir = self.project_dir / "out"
        self.temp_dir = self.output_dir / "tmp"
        self.utils_dir = self.project_dir / "utils"
        
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        self.extractor = FirmwareExtractor(self.utils_dir)
        self.git_manager = GitManager(self.output_dir)
        self.telegram = TelegramNotifier()
    
    async def run(self, firmware_path: str) -> None:
        UI.banner()
        UI.section("DumprX - Modern Firmware Extraction Tool")
        
        try:
            if self._is_url(firmware_path):
                file_path = await self._download_firmware(firmware_path)
                if not file_path:
                    UI.error("Download failed", 1)
            else:
                file_path = Path(firmware_path)
                if not file_path.exists():
                    UI.error(f"File not found: {firmware_path}", 1)
            
            await self._extract_firmware(file_path)
            device_info = await self._analyze_firmware()
            await self._upload_to_git(device_info)
            await self._send_notification(device_info)
            
            UI.success("Firmware processing completed successfully!")
            
        except KeyboardInterrupt:
            UI.warning("Operation cancelled by user")
            sys.exit(1)
        except Exception as e:
            UI.error(f"Unexpected error: {e}", 1)
    
    def _is_url(self, path: str) -> bool:
        return path.startswith(('http://', 'https://', 'ftp://'))
    
    async def _download_firmware(self, url: str) -> Optional[Path]:
        UI.section("Downloading Firmware")
        
        async with Downloader() as downloader:
            if not downloader.is_supported_url(url):
                UI.warning("URL may not be from a supported file host")
            
            downloaded_file = await downloader.download(url, str(self.input_dir))
            
            if downloaded_file:
                UI.success(f"Downloaded: {downloaded_file.name}")
                return downloaded_file
            else:
                UI.error("Download failed")
                return None
    
    async def _extract_firmware(self, file_path: Path) -> None:
        UI.section("Extracting Firmware")
        
        if file_path.is_dir():
            UI.info("Directory input detected, copying contents")
            shutil.copytree(file_path, self.temp_dir, dirs_exist_ok=True)
        else:
            success = await self.extractor.extract(file_path, self.temp_dir)
            if not success:
                UI.error("Extraction failed", 1)
        
        UI.success("Extraction completed")
    
    async def _analyze_firmware(self) -> Dict[str, str]:
        UI.section("Analyzing Firmware")
        
        device_info = {
            'brand': 'Unknown',
            'codename': 'Unknown',
            'platform': 'Unknown',
            'android_version': 'Unknown',
            'fingerprint': 'Unknown',
            'kernel_version': ''
        }
        
        build_prop_paths = [
            self.temp_dir / "system" / "build.prop",
            self.temp_dir / "build.prop",
            self.temp_dir / "system" / "system" / "build.prop"
        ]
        
        for build_prop in build_prop_paths:
            if build_prop.exists():
                device_info.update(await self._parse_build_prop(build_prop))
                break
        
        recovery_paths = [
            self.temp_dir / "recovery.img",
            self.temp_dir / "recovery",
            self.temp_dir / "boot" / "recovery.img"
        ]
        
        for recovery_path in recovery_paths:
            if recovery_path.exists():
                kernel_info = await self._extract_kernel_info(recovery_path)
                if kernel_info:
                    device_info['kernel_version'] = kernel_info
                break
        
        UI.info(f"Device: {device_info['brand']} {device_info['codename']}")
        UI.info(f"Platform: {device_info['platform']}")
        UI.info(f"Android: {device_info['android_version']}")
        
        return device_info
    
    async def _parse_build_prop(self, build_prop_path: Path) -> Dict[str, str]:
        info = {}
        
        try:
            with open(build_prop_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        
                        if key == 'ro.product.brand':
                            info['brand'] = value
                        elif key == 'ro.product.device':
                            info['codename'] = value
                        elif key == 'ro.board.platform':
                            info['platform'] = value
                        elif key == 'ro.build.version.release':
                            info['android_version'] = value
                        elif key == 'ro.build.fingerprint':
                            info['fingerprint'] = value
        except Exception as e:
            UI.warning(f"Failed to parse build.prop: {e}")
        
        return info
    
    async def _extract_kernel_info(self, recovery_path: Path) -> Optional[str]:
        try:
            if recovery_path.is_file():
                unpackboot = self.utils_dir / "unpackboot.sh"
                if unpackboot.exists():
                    process = await asyncio.create_subprocess_exec(
                        "bash", str(unpackboot), str(recovery_path), str(self.temp_dir / "recovery_extracted"),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await process.communicate()
                    
                    ikconfig_path = self.temp_dir / "recovery_extracted" / "ikconfig"
                    if ikconfig_path.exists():
                        with open(ikconfig_path, 'r') as f:
                            for line in f:
                                if "Kernel Configuration" in line:
                                    return line.split()[2]
        except:
            pass
        
        return None
    
    async def _upload_to_git(self, device_info: Dict[str, str]) -> None:
        UI.section("Uploading to Git Repository")
        
        await self._create_readme(device_info)
        
        success = await self.git_manager.setup_repository(device_info)
        if not success:
            UI.warning("Git upload failed or not configured")
    
    async def _create_readme(self, device_info: Dict[str, str]) -> None:
        readme_content = f"""# {device_info['brand']} {device_info['codename']} Firmware

## Device Information
- **Brand:** {device_info['brand']}
- **Device:** {device_info['codename']}
- **Platform:** {device_info['platform']}
- **Android Version:** {device_info['android_version']}
- **Fingerprint:** {device_info['fingerprint']}
"""
        
        if device_info['kernel_version']:
            readme_content += f"- **Kernel Version:** {device_info['kernel_version']}\n"
        
        readme_content += """
## Extraction Information
This firmware was extracted using DumprX, a modern firmware extraction toolkit.

## Contents
This repository contains the extracted firmware files and partition images.
"""
        
        readme_path = self.output_dir / "README.md"
        with open(readme_path, 'w') as f:
            f.write(readme_content)
    
    async def _send_notification(self, device_info: Dict[str, str]) -> None:
        UI.section("Sending Notification")
        
        repo_url = f"https://github.com/{device_info['brand']}_{device_info['codename']}"
        await self.telegram.send_notification(device_info, repo_url)
    
    def print_usage(self) -> None:
        UI.info("Usage: python3 dumprx.py <firmware_file_or_url>")
        UI.info("")
        UI.info("Supported formats:")
        supported_formats = config.get('extractors.supported_formats', [])
        for fmt in supported_formats:
            UI.info(f"  • {fmt}")
        UI.info("")
        UI.info("Supported URLs:")
        supported_hosts = config.get('urls.supported_hosts', [])
        for host in supported_hosts:
            UI.info(f"  • {host}")

def main():
    parser = argparse.ArgumentParser(description="DumprX - Modern Firmware Extraction Tool")
    parser.add_argument("firmware", nargs='?', help="Firmware file path or download URL")
    parser.add_argument("--config", default="config.yaml", help="Configuration file path")
    parser.add_argument("--version", action="version", version="DumprX 2.0")
    
    args = parser.parse_args()
    
    if not args.firmware:
        dumprx = DumprX()
        dumprx.print_usage()
        sys.exit(1)
    
    dumprx = DumprX()
    
    try:
        asyncio.run(dumprx.run(args.firmware))
    except KeyboardInterrupt:
        UI.warning("Operation cancelled")
        sys.exit(1)

if __name__ == "__main__":
    main()