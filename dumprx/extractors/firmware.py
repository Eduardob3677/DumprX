import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from dumprx.core.config import Config
from dumprx.utils.files import (
    get_file_type, is_url, safe_move, safe_copy, run_command, 
    extract_with_7z, calculate_sha1
)


class FirmwareExtractor:
    def __init__(self, config: Config, console: Console, verbose: bool = False):
        self.config = config
        self.console = console
        self.verbose = verbose
        self.tools = config.get_tool_paths()
    
    def extract(self, firmware_path: str) -> bool:
        if is_url(firmware_path):
            return self._extract_from_url(firmware_path)
        else:
            return self._extract_from_file(firmware_path)
    
    def _extract_from_url(self, url: str) -> bool:
        self.console.print(f"[blue]Downloading from URL: {url}[/blue]")
        downloaded_file = self._download_firmware(url)
        if not downloaded_file:
            return False
        return self._extract_from_file(str(downloaded_file))
    
    def _extract_from_file(self, filepath: str) -> bool:
        firmware_path = Path(filepath)
        
        if not firmware_path.exists():
            self.console.print(f"[red]Error: File not found: {filepath}[/red]")
            return False
        
        if firmware_path.is_dir():
            return self._process_directory(firmware_path)
        
        file_type = get_file_type(filepath)
        self.console.print(f"[blue]Detected file type: {file_type}[/blue]")
        
        if file_type == "archive":
            return self._extract_archive(firmware_path)
        elif file_type == "lg_kdz":
            return self._extract_lg_kdz(firmware_path)
        elif file_type == "encrypted_firmware":
            return self._extract_encrypted_firmware(firmware_path)
        elif file_type == "android_dat":
            return self._extract_android_dat(firmware_path)
        elif file_type == "ota_payload":
            return self._extract_ota_payload(firmware_path)
        elif file_type == "system_image":
            return self._process_system_image(firmware_path)
        else:
            self.console.print(f"[yellow]Warning: Unknown file type, trying generic extraction[/yellow]")
            return self._extract_generic(firmware_path)
    
    def _process_directory(self, directory: Path) -> bool:
        self.console.print(f"[blue]Processing directory: {directory}[/blue]")
        
        os.chdir(directory)
        copied_files = []
        
        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.stat().st_size > 10 * 1024 * 1024:
                dest_path = self.config.tmp_dir / file_path.name
                if safe_copy(file_path, dest_path):
                    copied_files.append(dest_path)
        
        os.chdir(self.config.tmp_dir)
        
        for copied_file in copied_files:
            if not self._extract_from_file(str(copied_file)):
                self.console.print(f"[yellow]Warning: Failed to extract {copied_file.name}[/yellow]")
        
        return True
    
    def _extract_archive(self, archive_path: Path) -> bool:
        self.console.print(f"[blue]Extracting archive: {archive_path.name}[/blue]")
        
        dest_path = self.config.tmp_dir / archive_path.name
        safe_copy(archive_path, dest_path)
        
        os.chdir(self.config.tmp_dir)
        
        if not extract_with_7z(dest_path, self.config.tmp_dir, self.tools["7zz"]):
            self.console.print(f"[red]Failed to extract archive: {archive_path.name}[/red]")
            return False
        
        return self._process_extracted_files()
    
    def _extract_lg_kdz(self, kdz_path: Path) -> bool:
        self.console.print("[blue]LG KDZ Detected[/blue]")
        
        dest_path = self.config.tmp_dir / kdz_path.name
        safe_move(kdz_path, dest_path) if kdz_path.parent == self.config.input_dir else safe_copy(kdz_path, dest_path)
        
        os.chdir(self.config.tmp_dir)
        
        success, _ = run_command([
            "python3", str(self.tools["kdz_extract"]), 
            "-f", kdz_path.name, "-x", "-o", "./"
        ])
        
        if not success:
            self.console.print("[red]Failed to extract KDZ file[/red]")
            return False
        
        dz_files = list(self.config.tmp_dir.glob("*.dz"))
        if dz_files:
            dz_file = dz_files[0]
            self.console.print("[blue]Extracting All Partitions As Individual Images[/blue]")
            
            success, _ = run_command([
                "python3", str(self.tools["dz_extract"]),
                "-f", dz_file.name, "-s", "-o", "./"
            ])
            
            if not success:
                self.console.print("[red]Failed to extract DZ file[/red]")
                return False
        
        return self._process_extracted_files()
    
    def _extract_encrypted_firmware(self, firmware_path: Path) -> bool:
        self.console.print(f"[blue]Processing encrypted firmware: {firmware_path.name}[/blue]")
        
        if ".ozip" in firmware_path.name:
            return self._extract_ozip(firmware_path)
        elif ".ofp" in firmware_path.name:
            return self._extract_ofp(firmware_path)
        elif ".ops" in firmware_path.name:
            return self._extract_ops(firmware_path)
        
        return False
    
    def _extract_ozip(self, ozip_path: Path) -> bool:
        dest_path = self.config.tmp_dir / ozip_path.name
        safe_copy(ozip_path, dest_path)
        
        os.chdir(self.config.tmp_dir)
        
        success, _ = run_command([
            "python3", str(self.tools["ozipdecrypt"]), dest_path.name
        ])
        
        return success and self._process_extracted_files()
    
    def _extract_android_dat(self, dat_path: Path) -> bool:
        self.console.print(f"[blue]Processing Android DAT file: {dat_path.name}[/blue]")
        
        transfer_list = dat_path.parent / dat_path.name.replace(".new.dat", ".transfer.list")
        if not transfer_list.exists():
            transfer_list = dat_path.parent / "system.transfer.list"
        
        if not transfer_list.exists():
            self.console.print("[red]Transfer list file not found[/red]")
            return False
        
        output_img = self.config.out_dir / "system.img"
        
        success, _ = run_command([
            "python3", str(self.tools["sdat2img"]),
            str(transfer_list), str(dat_path), str(output_img)
        ])
        
        return success
    
    def _extract_ota_payload(self, payload_path: Path) -> bool:
        self.console.print("[blue]Processing OTA payload[/blue]")
        
        dest_path = self.config.tmp_dir / payload_path.name
        safe_copy(payload_path, dest_path)
        
        os.chdir(self.config.tmp_dir)
        
        success, _ = run_command([
            str(self.tools["payload_extractor"]), "-o", "./", dest_path.name
        ])
        
        return success and self._process_extracted_files()
    
    def _process_system_image(self, image_path: Path) -> bool:
        self.console.print(f"[blue]Processing system image: {image_path.name}[/blue]")
        
        dest_path = self.config.out_dir / image_path.name
        safe_copy(image_path, dest_path)
        
        return True
    
    def _extract_generic(self, file_path: Path) -> bool:
        try:
            return self._extract_archive(file_path)
        except:
            self.console.print(f"[red]Failed to extract: {file_path.name}[/red]")
            return False
    
    def _process_extracted_files(self) -> bool:
        os.chdir(self.config.tmp_dir)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task("Processing extracted files...", total=100)
            
            for partition in self.config.partitions:
                self._process_partition(partition)
                progress.advance(task, 100 / len(self.config.partitions))
        
        self._generate_file_lists()
        return True
    
    def _process_partition(self, partition: str) -> None:
        img_files = list(self.config.tmp_dir.glob(f"{partition}.img"))
        
        for img_file in img_files:
            dest_path = self.config.out_dir / img_file.name
            
            if self.tools["simg2img"].exists():
                success, _ = run_command([
                    str(self.tools["simg2img"]), str(img_file), str(dest_path)
                ])
                if not success and img_file.exists():
                    safe_move(img_file, dest_path)
            else:
                safe_move(img_file, dest_path)
    
    def _generate_file_lists(self) -> None:
        self.console.print("[blue]Generating file lists...[/blue]")
        
        os.chdir(self.config.out_dir)
        
        all_files = []
        for file_path in Path(".").rglob("*"):
            if file_path.is_file() and ".git/" not in str(file_path):
                all_files.append(str(file_path))
        
        all_files.sort()
        
        all_files_txt = self.config.out_dir / "all_files.txt"
        with open(all_files_txt, "w") as f:
            f.write("\n".join(all_files))
    
    def _download_firmware(self, url: str) -> Optional[Path]:
        self.console.print(f"[yellow]URL download not yet implemented: {url}[/yellow]")
        return None
    
    def _extract_ofp(self, ofp_path: Path) -> bool:
        self.console.print("[yellow]OFP extraction not yet implemented[/yellow]")
        return False
    
    def _extract_ops(self, ops_path: Path) -> bool:
        self.console.print("[yellow]OPS extraction not yet implemented[/yellow]")
        return False