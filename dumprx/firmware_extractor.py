#!/usr/bin/env python3

import os
from pathlib import Path
from typing import Dict, Any, Optional

from rich.console import Console

from .utils import run_command, ProgressManager, copy_file_or_dir, move_file_or_dir
from .external_tools import ExternalToolManager
from .firmware_detector import FirmwareDetector

console = Console()

class FirmwareExtractor:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.input_dir = project_dir / "input"
        self.utils_dir = project_dir / "utils"
        self.output_dir = project_dir / "out"
        self.tmp_dir = self.output_dir / "tmp"
        
        self.tool_manager = ExternalToolManager(self.utils_dir)
        self.detector = FirmwareDetector(self.tool_manager)
        
        self.partitions = [
            "system", "system_ext", "system_other", "systemex", "vendor", "cust", 
            "odm", "oem", "factory", "product", "xrom", "modem", "dtbo", "dtb", 
            "boot", "vendor_boot", "recovery", "tz", "oppo_product", "preload_common"
        ]
    
    def extract_firmware(self, filepath: Path, output_dir: Optional[Path] = None) -> bool:
        if output_dir:
            self.output_dir = output_dir
            self.tmp_dir = self.output_dir / "tmp"
        
        # Setup directories
        self._setup_directories()
        
        # Detect firmware type
        firmware_info = self.detector.detect_firmware_type(filepath)
        console.print(f"[green]Detected:[/green] {firmware_info['format']}")
        
        # Extract based on type
        extractor_method = getattr(self, f"_extract_{firmware_info['type']}", None)
        if not extractor_method:
            console.print(f"[red]Unsupported firmware type: {firmware_info['type']}[/red]")
            return False
        
        try:
            return extractor_method(filepath, firmware_info)
        except Exception as e:
            console.print(f"[red]Extraction failed: {e}[/red]")
            return False
    
    def _setup_directories(self):
        # Cleanup tmp and recreate directories
        if self.tmp_dir.exists():
            import shutil
            shutil.rmtree(self.tmp_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
    
    def _extract_ozip(self, filepath: Path, info: Dict[str, Any]) -> bool:
        console.print("[blue]Decrypting OZIP file...[/blue]")
        
        # Copy file to tmp directory
        tmp_file = self.tmp_dir / filepath.name
        copy_file_or_dir(filepath, tmp_file)
        
        # Use oppo decrypt tool
        ozipdecrypt = self.tool_manager.get_tool_path("ozipdecrypt")
        requirements_file = self.utils_dir / "oppo_decrypt" / "requirements.txt"
        
        cmd = [
            "uv", "run", "--with-requirements", str(requirements_file),
            str(ozipdecrypt), str(tmp_file)
        ]
        
        result = run_command(cmd, cwd=self.tmp_dir, check=False)
        
        if result.returncode == 0:
            # Find extracted content
            zip_file = self.tmp_dir / f"{filepath.stem}.zip"
            if zip_file.exists():
                return self._extract_archive(zip_file, {'type': 'zip'})
            elif (self.tmp_dir / "out").exists():
                return self._process_extracted_directory(self.tmp_dir / "out")
        
        return False
    
    def _extract_ops(self, filepath: Path, info: Dict[str, Any]) -> bool:
        console.print("[blue]Decrypting OPS file...[/blue]")
        
        tmp_file = self.tmp_dir / filepath.name
        copy_file_or_dir(filepath, tmp_file)
        
        opsdecrypt = self.tool_manager.get_tool_path("opsdecrypt")
        requirements_file = self.utils_dir / "oppo_decrypt" / "requirements.txt"
        
        cmd = [
            "uv", "run", "--with-requirements", str(requirements_file),
            str(opsdecrypt), "decrypt", str(tmp_file)
        ]
        
        result = run_command(cmd, cwd=self.tmp_dir, check=False)
        
        if result.returncode == 0 and (self.tmp_dir / "extract").exists():
            return self._process_extracted_directory(self.tmp_dir / "extract")
        
        return False
    
    def _extract_kdz(self, filepath: Path, info: Dict[str, Any]) -> bool:
        console.print("[blue]Extracting LG KDZ file...[/blue]")
        
        tmp_file = self.tmp_dir / filepath.name
        copy_file_or_dir(filepath, tmp_file)
        
        # Extract KDZ
        kdz_extract = self.tool_manager.get_tool_path("kdz_extract")
        cmd = ["python3", str(kdz_extract), "-f", str(tmp_file), "-x", "-o", "./"]
        run_command(cmd, cwd=self.tmp_dir)
        
        # Find and extract DZ file
        dz_files = list(self.tmp_dir.glob("*.dz"))
        if dz_files:
            console.print("[blue]Extracting DZ partitions...[/blue]")
            dz_extract = self.tool_manager.get_tool_path("dz_extract")
            cmd = ["python3", str(dz_extract), "-f", str(dz_files[0]), "-s", "-o", "./"]
            run_command(cmd, cwd=self.tmp_dir)
            return True
        
        return False
    
    def _extract_archive(self, filepath: Path, info: Dict[str, Any]) -> bool:
        console.print(f"[blue]Extracting {info.get('archive_type', 'archive')} file...[/blue]")
        
        bin_7zz = self.tool_manager.get_tool_path("7zz")
        
        # Check for special content first
        result = run_command([str(bin_7zz), "l", "-ba", str(filepath)], 
                           capture_output=True, check=False)
        
        if result.returncode == 0:
            contents = result.stdout
            
            # Handle payload.bin
            if "payload.bin" in contents:
                return self._extract_ota_payload(filepath)
            
            # Handle UPDATE.APP
            elif "UPDATE.APP" in contents:
                return self._extract_huawei_update(filepath)
            
            # Handle OPS files in archive
            elif ".ops" in contents:
                return self._extract_ops_archive(filepath)
        
        # Standard archive extraction
        cmd = [str(bin_7zz), "x", "-y", str(filepath)]
        result = run_command(cmd, cwd=self.tmp_dir, check=False)
        
        if result.returncode == 0:
            return self._process_extracted_directory(self.tmp_dir)
        
        return False
    
    def _extract_ota_payload(self, filepath: Path) -> bool:
        console.print("[blue]Extracting Android OTA Payload...[/blue]")
        
        payload_extractor = self.tool_manager.get_tool_path("payload_extractor")
        nproc_result = run_command(["nproc", "--all"], capture_output=True)
        nproc = nproc_result.stdout.strip() if nproc_result.returncode == 0 else "4"
        
        cmd = [str(payload_extractor), "-c", nproc, "-o", str(self.tmp_dir), str(filepath)]
        result = run_command(cmd, check=False)
        
        return result.returncode == 0
    
    def _extract_huawei_update(self, filepath: Path) -> bool:
        console.print("[blue]Extracting Huawei UPDATE.APP...[/blue]")
        
        bin_7zz = self.tool_manager.get_tool_path("7zz")
        
        # Extract UPDATE.APP first
        cmd = [str(bin_7zz), "x", str(filepath), "UPDATE.APP"]
        run_command(cmd, cwd=self.tmp_dir)
        
        update_app = self.tmp_dir / "UPDATE.APP"
        if update_app.exists():
            splituapp = self.tool_manager.get_tool_path("splituapp")
            
            # Try to extract super partitions first
            cmd = ["python3", str(splituapp), "-f", "UPDATE.APP", "-l", "super", "preas", "preavs"]
            result = run_command(cmd, cwd=self.tmp_dir, check=False)
            
            if result.returncode != 0:
                # Extract individual partitions
                for partition in self.partitions:
                    cmd = ["python3", str(splituapp), "-f", "UPDATE.APP", "-l", partition.replace(".img", "")]
                    run_command(cmd, cwd=self.tmp_dir, check=False)
            
            return True
        
        return False
    
    def _extract_ops_archive(self, filepath: Path) -> bool:
        console.print("[blue]Extracting OPS from archive...[/blue]")
        
        bin_7zz = self.tool_manager.get_tool_path("7zz")
        
        # List and extract .ops files
        result = run_command([str(bin_7zz), "l", "-ba", str(filepath)], capture_output=True)
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            ops_files = [line.split()[-1] for line in lines if '.ops' in line]
            
            for ops_file in ops_files:
                cmd = [str(bin_7zz), "e", "-y", str(filepath), ops_file]
                run_command(cmd, cwd=self.tmp_dir)
            
            # Process extracted OPS files
            for ops_file in self.tmp_dir.glob("*.ops"):
                self._extract_ops(ops_file, {'type': 'ops'})
            
            return True
        
        return False
    
    def _extract_super_image(self, filepath: Path, info: Dict[str, Any]) -> bool:
        console.print("[blue]Extracting Android Super Image...[/blue]")
        return self._extract_super_partitions(filepath)
    
    def _extract_super_partitions(self, super_img: Path) -> bool:
        simg2img = self.tool_manager.get_tool_path("simg2img")
        lpunpack = self.tool_manager.get_tool_path("lpunpack")
        
        # Convert sparse image to raw if needed
        super_raw = self.tmp_dir / "super.img.raw"
        cmd = [str(simg2img), str(super_img), str(super_raw)]
        result = run_command(cmd, cwd=self.tmp_dir, check=False)
        
        if result.returncode != 0 and super_img.exists():
            # Copy as raw if conversion failed
            copy_file_or_dir(super_img, super_raw)
        
        if super_raw.exists():
            # Extract partitions
            for partition in self.partitions:
                for suffix in ["_a", ""]:
                    partition_name = f"{partition}{suffix}"
                    cmd = [str(lpunpack), f"--partition={partition_name}", str(super_raw)]
                    result = run_command(cmd, cwd=self.tmp_dir, check=False)
                    
                    if result.returncode == 0:
                        # Rename _a partition to base name
                        if suffix == "_a":
                            a_file = self.tmp_dir / f"{partition}_a.img"
                            base_file = self.tmp_dir / f"{partition}.img"
                            if a_file.exists():
                                move_file_or_dir(a_file, base_file)
                        break
            
            # Cleanup
            if super_raw.exists():
                super_raw.unlink()
            
            return True
        
        return False
    
    def _extract_nb0(self, filepath: Path, info: Dict[str, Any]) -> bool:
        console.print("[blue]Extracting Nokia NB0 firmware...[/blue]")
        
        nb0_extract = self.tool_manager.get_tool_path("nb0_extract")
        cmd = [str(nb0_extract), str(filepath)]
        result = run_command(cmd, cwd=self.tmp_dir, check=False)
        
        return result.returncode == 0
    
    def _extract_pac(self, filepath: Path, info: Dict[str, Any]) -> bool:
        console.print("[blue]Extracting Spreadtrum PAC...[/blue]")
        
        pacextractor = self.tool_manager.get_tool_path("pacextractor")
        cmd = ["python3", str(pacextractor), str(filepath)]
        result = run_command(cmd, cwd=self.tmp_dir, check=False)
        
        return result.returncode == 0
    
    def _extract_sin(self, filepath: Path, info: Dict[str, Any]) -> bool:
        console.print("[blue]Extracting Sony SIN...[/blue]")
        
        unsin = self.tool_manager.get_tool_path("unsin")
        cmd = [str(unsin), str(filepath)]
        result = run_command(cmd, cwd=self.tmp_dir, check=False)
        
        return result.returncode == 0
    
    def _extract_ruu(self, filepath: Path, info: Dict[str, Any]) -> bool:
        console.print("[blue]Extracting HTC RUU...[/blue]")
        
        ruu_decrypt = self.tool_manager.get_tool_path("ruu_decrypt")
        cmd = [str(ruu_decrypt), str(filepath)]
        result = run_command(cmd, cwd=self.tmp_dir, check=False)
        
        return result.returncode == 0
    
    def _process_extracted_directory(self, directory: Path) -> bool:
        # Move all extracted content to output directory
        for item in directory.iterdir():
            dst = self.output_dir / item.name
            if dst.exists():
                if dst.is_dir():
                    import shutil
                    shutil.rmtree(dst)
                else:
                    dst.unlink()
            move_file_or_dir(item, dst)
        
        return True
    
    def _extract_firmware_directory(self, dirpath: Path, info: Dict[str, Any]) -> bool:
        console.print("[blue]Processing firmware directory...[/blue]")
        
        # Copy entire directory to tmp for processing
        for item in dirpath.iterdir():
            dst = self.tmp_dir / item.name
            copy_file_or_dir(item, dst)
        
        return self._process_extracted_directory(self.tmp_dir)
    
    def _extract_directory(self, dirpath: Path, info: Dict[str, Any]) -> bool:
        return self._extract_firmware_directory(dirpath, info)
    
    def _extract_unknown(self, filepath: Path, info: Dict[str, Any]) -> bool:
        console.print(f"[red]Unknown firmware format: {filepath}[/red]")
        return False