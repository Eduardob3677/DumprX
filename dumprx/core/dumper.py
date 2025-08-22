import os
import shutil
import re
from pathlib import Path
from typing import Union, Optional
from rich.console import Console
from rich.progress import Progress

from dumprx.extractors.firmware_extractors import FirmwareExtractorFactory
from dumprx.utils.git_manager import GitManager
from dumprx.utils.device_info import DeviceInfoExtractor

class FirmwareDumper:
    def __init__(self, config, tool_manager, detector, progress, console):
        self.config = config
        self.tool_manager = tool_manager
        self.detector = detector
        self.progress = progress
        self.console = console
        
        self.extractor_factory = FirmwareExtractorFactory(config, tool_manager, console)
        self.git_manager = GitManager(config, console)
        self.device_info = DeviceInfoExtractor(config, console)
        
    def process_firmware(self, firmware_input: Union[Path, str], verbose: bool = False, no_upload: bool = False) -> bool:
        try:
            self.console.print(f"[blue]🔍 Processing firmware: {firmware_input}[/blue]")
            
            if isinstance(firmware_input, str) and not os.path.exists(firmware_input):
                firmware_path = self._download_firmware(firmware_input)
                if not firmware_path:
                    return False
            else:
                firmware_path = Path(firmware_input)
            
            file_info = self.detector.get_file_info(firmware_path)
            
            if not self.detector.is_supported_format(firmware_path):
                self.console.print(f"[red]❌ Unsupported firmware format: {file_info['type']}[/red]")
                return False
            
            self._clean_workspace()
            
            extractor = self.extractor_factory.get_extractor(file_info['type'])
            if not extractor:
                self.console.print(f"[red]❌ No extractor available for: {file_info['type']}[/red]")
                return False
            
            extraction_success = extractor.extract(firmware_path, self.config.tmp_dir)
            if not extraction_success:
                self.console.print("[red]❌ Firmware extraction failed[/red]")
                return False
            
            self._process_extracted_files()
            
            device_data = self.device_info.extract_device_info(self.config.output_dir)
            
            if device_data and not no_upload:
                upload_success = self.git_manager.upload_firmware(device_data, self.config.output_dir)
                if upload_success:
                    self.console.print("[green]✅ Firmware uploaded to repository[/green]")
                else:
                    self.console.print("[yellow]⚠️  Firmware extracted but upload failed[/yellow]")
            
            self._cleanup_temp_files()
            
            return True
            
        except Exception as e:
            self.console.print(f"[red]💥 Error processing firmware: {str(e)}[/red]")
            if verbose:
                self.console.print_exception()
            return False
    
    def _download_firmware(self, url: str) -> Optional[Path]:
        self.console.print(f"[blue]📥 Downloading firmware from: {url}[/blue]")
        
        try:
            from dumprx.utils.downloaders import DownloadManager
            download_manager = DownloadManager(self.config, self.console)
            
            downloaded_file = download_manager.download(url, self.config.input_dir)
            if downloaded_file:
                self.console.print(f"[green]✅ Download completed: {downloaded_file.name}[/green]")
                return downloaded_file
            else:
                self.console.print("[red]❌ Download failed[/red]")
                return None
                
        except Exception as e:
            self.console.print(f"[red]💥 Download error: {str(e)}[/red]")
            return None
    
    def _clean_workspace(self):
        if self.config.tmp_dir.exists():
            shutil.rmtree(self.config.tmp_dir)
        self.config.tmp_dir.mkdir(parents=True, exist_ok=True)
        
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _process_extracted_files(self):
        self.console.print("[blue]🔧 Processing extracted files...[/blue]")
        
        os.chdir(self.config.tmp_dir)
        
        self._extract_system_images()
        self._extract_boot_images()
        self._process_super_images()
        self._move_final_images()
    
    def _extract_system_images(self):
        for partition in self.config.ext4_partitions:
            img_file = self.config.tmp_dir / f"{partition}.img"
            if img_file.exists():
                self.console.print(f"[cyan]📦 Extracting {partition} partition...[/cyan]")
                
                output_dir = self.config.output_dir / partition
                output_dir.mkdir(parents=True, exist_ok=True)
                
                try:
                    if self._is_sparse_image(img_file):
                        raw_img = self.config.tmp_dir / f"{partition}.img.raw"
                        self.tool_manager.run_command([
                            str(self.config.tool_paths['simg2img']),
                            str(img_file), str(raw_img)
                        ])
                        img_file = raw_img
                    
                    self.tool_manager.run_command([
                        "python3", str(self.config.tool_paths['sdat2img']),
                        str(img_file), str(output_dir)
                    ])
                    
                except Exception as e:
                    self.console.print(f"[yellow]⚠️  Failed to extract {partition}: {str(e)}[/yellow]")
    
    def _extract_boot_images(self):
        from dumprx.extractors.boot_unpacker import BootImageUnpacker
        boot_unpacker = BootImageUnpacker(self.config)
        
        for boot_type in ['boot', 'recovery', 'vendor_boot']:
            img_file = self.config.tmp_dir / f"{boot_type}.img"
            if img_file.exists():
                self.console.print(f"[cyan]🥾 Extracting {boot_type} image...[/cyan]")
                
                output_dir = self.config.output_dir / f"{boot_type}RE"
                output_dir.mkdir(parents=True, exist_ok=True)
                
                try:
                    boot_unpacker.unpack_boot_image(img_file, output_dir)
                except Exception as e:
                    self.console.print(f"[yellow]⚠️  Failed to extract {boot_type}: {str(e)}[/yellow]")
    
    def _process_super_images(self):
        super_img = self.config.tmp_dir / "super.img"
        if super_img.exists():
            self.console.print("[cyan]🔄 Processing super partition...[/cyan]")
            
            try:
                if self._is_sparse_image(super_img):
                    raw_super = self.config.tmp_dir / "super.img.raw"
                    self.tool_manager.run_command([
                        str(self.config.tool_paths['simg2img']),
                        str(super_img), str(raw_super)
                    ])
                    super_img = raw_super
                
                for partition in self.config.partitions:
                    try:
                        self.tool_manager.run_command([
                            str(self.config.tool_paths['lpunpack']),
                            f"--partition={partition}_a",
                            str(super_img)
                        ])
                        
                        part_a = self.config.tmp_dir / f"{partition}_a.img"
                        part_img = self.config.tmp_dir / f"{partition}.img"
                        
                        if part_a.exists():
                            part_a.rename(part_img)
                            
                    except:
                        try:
                            self.tool_manager.run_command([
                                str(self.config.tool_paths['lpunpack']),
                                f"--partition={partition}",
                                str(super_img)
                            ])
                        except:
                            continue
                
            except Exception as e:
                self.console.print(f"[yellow]⚠️  Failed to process super partition: {str(e)}[/yellow]")
    
    def _move_final_images(self):
        for item in self.config.tmp_dir.iterdir():
            if item.is_file() and item.suffix in ['.img', '.bin', '.elf']:
                dest = self.config.output_dir / item.name
                try:
                    shutil.move(str(item), str(dest))
                except Exception:
                    continue
    
    def _is_sparse_image(self, img_file: Path) -> bool:
        try:
            with open(img_file, 'rb') as f:
                header = f.read(4)
                return header == b'\x3a\xff\x26\xed'
        except Exception:
            return False
    
    def _cleanup_temp_files(self):
        try:
            if self.config.tmp_dir.exists():
                journal_files = list(self.config.tmp_dir.rglob("*journal*"))
                for journal in journal_files:
                    journal.unlink(missing_ok=True)
        except Exception:
            pass