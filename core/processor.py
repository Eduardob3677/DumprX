import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Union

from core.config import Config
from core.device import DeviceInfo
from extractors.manager import ExtractorManager
from utils.console import Console
from utils.git import GitManager
from utils.telegram import TelegramNotifier


class FirmwareProcessor:
    def __init__(self, firmware_path: Union[str, Path], output_dir: Union[str, Path], config: Config):
        self.firmware_path = Path(firmware_path)
        self.output_dir = Path(output_dir)
        self.config = config
        self.console = Console()
        
        self.input_dir = Path("input")
        self.tmp_dir = self.output_dir / "tmp"
        self.utils_dir = Path("bin")
        
        self._setup_directories()
    
    def _setup_directories(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        if self.tmp_dir.exists():
            shutil.rmtree(self.tmp_dir)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
    
    def process(self):
        self.console.info(f"Extracting firmware: {self.firmware_path}")
        
        if str(self.firmware_path).startswith(('http://', 'https://', 'ftp://')):
            firmware_path = self._download_firmware()
        else:
            firmware_path = self.firmware_path
        
        extracted_path = self._extract_firmware(firmware_path)
        device_info = DeviceInfo(extracted_path)
        
        self.console.info(f"Device: {device_info.brand} {device_info.codename}")
        self.console.info(f"Android: {device_info.android_version}")
        
        self._process_extracted_files(extracted_path)
        self._create_repository(extracted_path, device_info)
        self._send_notifications(device_info)
        
        self.console.success("Processing completed successfully")
    
    def _download_firmware(self) -> Path:
        from downloaders.manager import DownloadManager
        
        self.input_dir.mkdir(parents=True, exist_ok=True)
        manager = DownloadManager(str(self.input_dir))
        return Path(manager.download(str(self.firmware_path)))
    
    def _extract_firmware(self, firmware_path: Path) -> Path:
        extractor = ExtractorManager(
            output_dir=self.tmp_dir,
            utils_dir=self.utils_dir
        )
        return extractor.extract(firmware_path)
    
    def _process_extracted_files(self, extracted_path: Path):
        self.console.info("Processing extracted files...")
        
        os.chdir(self.tmp_dir)
        
        self._cleanup_extracted_files()
        self._split_large_files()
    
    def _cleanup_extracted_files(self):
        patterns_to_remove = [
            "*sensetime*",
            "*.lic",
            "*[SYS]*"
        ]
        
        for pattern in patterns_to_remove:
            for path in self.tmp_dir.rglob(pattern):
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                elif path.is_file():
                    path.unlink(missing_ok=True)
    
    def _split_large_files(self):
        large_files = []
        for file_path in self.tmp_dir.rglob('*'):
            if file_path.is_file() and file_path.stat().st_size > 62 * 1024 * 1024:
                large_files.append(file_path)
        
        if large_files:
            self._create_split_script(large_files)
    
    def _create_split_script(self, large_files: list):
        script_path = self.tmp_dir / "join_split_files.sh"
        with open(script_path, 'w') as f:
            f.write("#!/bin/bash\\n\\n")
            
            for file_path in large_files:
                rel_path = file_path.relative_to(self.tmp_dir)
                f.write(f"cat {rel_path}.* 2>/dev/null >> {rel_path}\\n")
                f.write(f"rm -f {rel_path}.* 2>/dev/null\\n")
        
        script_path.chmod(0o755)
    
    def _create_repository(self, extracted_path: Path, device_info: DeviceInfo):
        if not (self.config.github_token or self.config.gitlab_token):
            self.console.warning("No Git token configured, skipping repository creation")
            return
        
        git_manager = GitManager(
            output_dir=self.tmp_dir,
            config=self.config
        )
        
        git_manager.create_repository(device_info)
    
    def _send_notifications(self, device_info: DeviceInfo):
        if self.config.telegram_token:
            notifier = TelegramNotifier(
                token=self.config.telegram_token,
                chat_id=self.config.telegram_chat
            )
            notifier.send_completion_notification(device_info, self.config)