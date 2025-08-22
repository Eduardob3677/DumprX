import os
import sys
import subprocess
import shutil
from pathlib import Path
from urllib.parse import urlparse
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from dumprx.downloaders.downloader_manager import DownloaderManager
from dumprx.extractors.extractor_manager import ExtractorManager
from dumprx.modules.git_manager import GitManager
from dumprx.modules.device_detector import DeviceDetector
from dumprx.utils.external_tools import ExternalToolsManager
from dumprx.utils.file_utils import FileUtils
from dumprx.core import get_project_root, get_output_dir, get_temp_dir, get_bin_dir, get_utils_dir

class FirmwareProcessor:
    def __init__(self, console=None, progress=None, github_token=None, telegram_token=None, chat_id=None, verbose=False):
        self.console = console or Console()
        self.progress = progress
        self.github_token = github_token
        self.telegram_token = telegram_token
        self.chat_id = chat_id
        self.verbose = verbose
        
        self.project_root = get_project_root()
        self.output_dir = get_output_dir()
        self.temp_dir = get_temp_dir()
        self.bin_dir = get_bin_dir()
        self.utils_dir = get_utils_dir()
        
        self.downloader = DownloaderManager(self.console, self.verbose)
        self.extractor = ExtractorManager(self.console, self.temp_dir, self.bin_dir, self.utils_dir, self.verbose)
        self.external_tools = ExternalToolsManager(self.utils_dir, self.console, self.verbose)
        self.device_detector = DeviceDetector(self.console, self.verbose)
        self.git_manager = GitManager(self.output_dir, self.github_token, self.console, self.verbose)
        
    def process_firmware(self, firmware_source, output_dir=None):
        try:
            if output_dir:
                self.output_dir = Path(output_dir)
                self.output_dir.mkdir(parents=True, exist_ok=True)
            
            self.console.print(f"\n[blue]🔍 Analyzing firmware source: {firmware_source}[/blue]")
            
            if self._is_url(firmware_source):
                firmware_path = self._download_firmware(firmware_source)
                if not firmware_path:
                    return False
            else:
                firmware_path = Path(firmware_source)
                if not firmware_path.exists():
                    self.console.print(f"[red]❌ File not found: {firmware_path}[/red]")
                    return False
            
            self.console.print(f"[green]📁 Processing firmware file: {firmware_path}[/green]")
            
            self.external_tools.setup_tools()
            
            extracted_path = self.extractor.extract_firmware(firmware_path)
            if not extracted_path:
                return False
            
            device_info = self.device_detector.detect_device(extracted_path)
            
            if device_info:
                self.console.print(Panel(
                    f"[bold green]📱 Device Detected[/bold green]\n"
                    f"Brand: {device_info.get('brand', 'Unknown')}\n"
                    f"Model: {device_info.get('model', 'Unknown')}\n"
                    f"Codename: {device_info.get('codename', 'Unknown')}\n"
                    f"Android Version: {device_info.get('android_version', 'Unknown')}",
                    border_style="green"
                ))
            
            self._process_partitions(extracted_path)
            
            self._generate_metadata(device_info)
            
            if self.github_token:
                self.git_manager.upload_dump(device_info)
            
            self.console.print("[bold green]✅ Firmware processing completed successfully![/bold green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]❌ Error processing firmware: {str(e)}[/red]")
            if self.verbose:
                self.console.print_exception()
            return False
    
    def _is_url(self, source):
        try:
            result = urlparse(source)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _download_firmware(self, url):
        try:
            return self.downloader.download(url, self.temp_dir / "input")
        except Exception as e:
            self.console.print(f"[red]❌ Download failed: {str(e)}[/red]")
            return None
    
    def _process_partitions(self, extracted_path):
        self.console.print("\n[blue]🔧 Processing partitions...[/blue]")
        
        supported_partitions = [
            "system", "system_ext", "vendor", "product", "odm", "boot", 
            "recovery", "dtbo", "dtb", "modem", "vendor_boot", "init_boot"
        ]
        
        for partition in supported_partitions:
            partition_files = list(extracted_path.glob(f"**/{partition}.*"))
            if partition_files:
                self.console.print(f"[green]📁 Found {partition} partition[/green]")
                for partition_file in partition_files:
                    self._process_partition_file(partition_file, partition)
    
    def _process_partition_file(self, partition_file, partition_name):
        try:
            if partition_file.suffix in ['.img', '.bin']:
                self.extractor.extract_partition_image(partition_file, partition_name)
            elif partition_file.suffix in ['.new.dat', '.new.dat.br']:
                self.extractor.convert_sparse_data(partition_file, partition_name)
        except Exception as e:
            if self.verbose:
                self.console.print(f"[yellow]⚠️  Failed to process {partition_file}: {str(e)}[/yellow]")
    
    def _generate_metadata(self, device_info):
        self.console.print("\n[blue]📝 Generating metadata files...[/blue]")
        
        try:
            metadata = {
                "device_info": device_info or {},
                "extraction_timestamp": str(Path().cwd()),
                "dumprx_version": "2.0.0"
            }
            
            import json
            metadata_file = self.output_dir / "dump_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            self.console.print(f"[green]✅ Metadata saved to {metadata_file}[/green]")
            
        except Exception as e:
            if self.verbose:
                self.console.print(f"[yellow]⚠️  Failed to generate metadata: {str(e)}[/yellow]")