"""
Main firmware dumper logic - orchestrates the entire firmware processing workflow.

This module contains the core business logic for downloading, extracting, and processing firmware.
"""

import os
import shutil
from pathlib import Path
from typing import Union, Optional, List
from dataclasses import dataclass
from urllib.parse import urlparse

from dumprxconfig import Config
from dumprxdevice_info import DeviceInfo
from dumprxdownloaders import get_downloader
from dumprxextractors import get_extractor
from dumprxmodules.validator import validate_url, validate_file_format, detect_url_service, get_file_format_info
from dumprxutils.console import print_info, print_error, print_success, print_step, print_substep, print_warning
from dumprxutils.git import GitManager
from dumprxutils.file_handler import FileHandler


@dataclass
class DumpResult:
    """Result of firmware dump operation."""
    success: bool
    output_dir: Optional[Path] = None
    git_repo_url: Optional[str] = None
    device_info: Optional[DeviceInfo] = None
    extracted_files: List[Path] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.extracted_files is None:
            self.extracted_files = []


class FirmwareDumper:
    """Main firmware dumper class."""
    
    def __init__(self, config: Config):
        self.config = config
        self.file_handler = FileHandler(config.project_dir)
        self.git_manager = GitManager(config)
        
        # Ensure required directories exist
        config.ensure_directories()
    
    def process_firmware(self, firmware_input: Union[str, Path], 
                        download_only: bool = False,
                        extract_only: bool = False,
                        create_git_repo: bool = True,
                        upload_to_git: bool = True) -> DumpResult:
        """
        Process firmware from various sources.
        
        Args:
            firmware_input: File path, directory path, or URL
            download_only: Only download, don't extract
            extract_only: Only extract, don't download
            create_git_repo: Whether to create git repository
            upload_to_git: Whether to upload to git hosting
            
        Returns:
            DumpResult with operation status
        """
        try:
            print_step("Starting Firmware Processing")
            
            # Determine input type and process accordingly
            input_path = Path(firmware_input) if not isinstance(firmware_input, Path) else firmware_input
            
            if validate_url(str(firmware_input)):
                # URL input
                return self._process_url(
                    str(firmware_input),
                    download_only=download_only,
                    extract_only=extract_only,
                    create_git_repo=create_git_repo,
                    upload_to_git=upload_to_git
                )
            elif input_path.is_file():
                # File input
                return self._process_file(
                    input_path,
                    extract_only=True,  # Files don't need downloading
                    create_git_repo=create_git_repo,
                    upload_to_git=upload_to_git
                )
            elif input_path.is_dir():
                # Directory input (already extracted)
                return self._process_directory(
                    input_path,
                    create_git_repo=create_git_repo,
                    upload_to_git=upload_to_git
                )
            else:
                return DumpResult(success=False, error=f"Invalid input: {firmware_input}")
                
        except Exception as e:
            error_msg = f"Firmware processing failed: {e}"
            print_error(error_msg)
            return DumpResult(success=False, error=error_msg)
    
    def _process_url(self, url: str, download_only: bool = False,
                    extract_only: bool = False, create_git_repo: bool = True,
                    upload_to_git: bool = True) -> DumpResult:
        """Process firmware from URL."""
        print_step("Processing URL", url)
        
        # Detect service
        service = detect_url_service(url)
        if not service:
            return DumpResult(success=False, error=f"Unsupported URL service: {url}")
        
        print_substep("Detected Service", service)
        
        # Download file
        downloader = get_downloader(url, service)
        if not downloader:
            return DumpResult(success=False, error=f"No downloader available for: {service}")
        
        download_result = downloader.download(url, self.config.input_dir)
        if not download_result.success:
            return DumpResult(success=False, error=f"Download failed: {download_result.error}")
        
        print_success(f"Downloaded: {download_result.filepath}")
        
        if download_only:
            return DumpResult(
                success=True,
                output_dir=download_result.filepath.parent,
                extracted_files=[download_result.filepath]
            )
        
        # Continue with extraction
        return self._process_file(
            download_result.filepath,
            extract_only=True,
            create_git_repo=create_git_repo,
            upload_to_git=upload_to_git
        )
    
    def _process_file(self, file_path: Path, extract_only: bool = False,
                     create_git_repo: bool = True, upload_to_git: bool = True) -> DumpResult:
        """Process firmware file."""
        print_step("Processing File", str(file_path))
        
        # Validate file format
        if not validate_file_format(file_path):
            return DumpResult(success=False, error=f"Unsupported file format: {file_path}")
        
        # Get format information
        format_info = get_file_format_info(file_path)
        print_substep("File Format", f"{format_info['format_type']} ({format_info['extraction_method']})")
        
        # Create output directory
        output_dir = self.config.output_dir / file_path.stem
        self.file_handler.ensure_directory(output_dir)
        
        # Extract file
        extractor = get_extractor(str(file_path), format_info['format_type'])
        if not extractor:
            return DumpResult(success=False, error=f"No extractor available for: {format_info['format_type']}")
        
        extraction_result = extractor.extract(file_path, output_dir)
        if not extraction_result.success:
            return DumpResult(success=False, error=f"Extraction failed: {extraction_result.error}")
        
        print_success(f"Extracted to: {extraction_result.output_dir}")
        
        # Continue with processing extracted directory
        return self._process_directory(
            extraction_result.output_dir,
            create_git_repo=create_git_repo,
            upload_to_git=upload_to_git,
            extracted_files=extraction_result.extracted_files
        )
    
    def _process_directory(self, directory: Path, create_git_repo: bool = True,
                          upload_to_git: bool = True, extracted_files: Optional[List[Path]] = None) -> DumpResult:
        """Process extracted firmware directory."""
        print_step("Processing Directory", str(directory))
        
        if extracted_files is None:
            extracted_files = []
        
        # Extract device information
        device_info = DeviceInfo.from_build_props(directory)
        print_substep("Device Detected", str(device_info))
        
        # Process firmware partitions
        self._process_firmware_partitions(directory)
        
        # Create board-info.txt
        self._create_board_info(directory, device_info)
        
        git_repo_url = None
        
        if create_git_repo:
            # Initialize git repository
            git_result = self.git_manager.initialize_repository(directory, device_info)
            if git_result.success:
                print_success("Git repository initialized")
                
                # Commit firmware dump
                commit_result = self.git_manager.commit_firmware_dump(device_info, [])
                if commit_result.success:
                    print_success("Firmware dump committed")
                    
                    if upload_to_git:
                        # Create remote repository
                        repo_name = device_info.get_repo_name()
                        remote_result = self.git_manager.create_remote_repository(repo_name, device_info)
                        
                        if remote_result.success:
                            git_repo_url = remote_result.repo_url
                            print_success(f"Remote repository created: {git_repo_url}")
                            
                            # Push to remote
                            push_result = self.git_manager.push_to_remote(git_repo_url)
                            if push_result.success:
                                print_success("Pushed to remote repository")
                            else:
                                print_warning(f"Failed to push: {push_result.error}")
                        else:
                            print_warning(f"Failed to create remote repo: {remote_result.error}")
                else:
                    print_warning(f"Failed to commit: {commit_result.error}")
            else:
                print_warning(f"Failed to initialize git: {git_result.error}")
        
        return DumpResult(
            success=True,
            output_dir=directory,
            git_repo_url=git_repo_url,
            device_info=device_info,
            extracted_files=extracted_files
        )
    
    def _process_firmware_partitions(self, directory: Path):
        """Process and extract firmware partitions."""
        print_step("Processing Firmware Partitions")
        
        # Look for common partition images
        partition_patterns = [
            'boot.img', 'recovery.img', 'system.img', 'vendor.img',
            'product.img', 'system_ext.img', 'odm.img', 'dtbo.img'
        ]
        
        for pattern in partition_patterns:
            partition_files = list(directory.glob(pattern))
            for partition_file in partition_files:
                self._process_partition_image(partition_file, directory)
    
    def _process_partition_image(self, partition_file: Path, output_dir: Path):
        """Process individual partition image."""
        partition_name = partition_file.stem
        print_substep("Processing Partition", partition_name)
        
        # Create partition directory
        partition_dir = output_dir / partition_name
        partition_dir.mkdir(exist_ok=True)
        
        # Try to extract partition using various methods
        if self._extract_with_7zip(partition_file, partition_dir):
            print_substep("Extracted with 7zip", partition_name)
            # Remove original image if extraction successful
            try:
                partition_file.unlink()
            except:
                pass
        elif self._extract_with_mount(partition_file, partition_dir):
            print_substep("Extracted with mount", partition_name)
            try:
                partition_file.unlink()
            except:
                pass
        else:
            print_warning(f"Could not extract partition: {partition_name}")
    
    def _extract_with_7zip(self, image_file: Path, output_dir: Path) -> bool:
        """Try to extract partition image with 7zip."""
        import subprocess
        
        try:
            # Try using 7z command
            result = subprocess.run([
                '7z', 'x', '-y', str(image_file), f'-o{output_dir}'
            ], capture_output=True, timeout=300)
            
            return result.returncode == 0
        except:
            return False
    
    def _extract_with_mount(self, image_file: Path, output_dir: Path) -> bool:
        """Try to extract partition image with mount (Linux only)."""
        import subprocess
        import platform
        
        if platform.system() != 'Linux':
            return False
        
        try:
            # Create temporary mount point
            mount_point = output_dir.parent / f"{output_dir.name}_mount"
            mount_point.mkdir(exist_ok=True)
            
            # Try to mount the image
            mount_result = subprocess.run([
                'sudo', 'mount', '-o', 'loop,ro', str(image_file), str(mount_point)
            ], capture_output=True, timeout=60)
            
            if mount_result.returncode == 0:
                # Copy contents
                copy_result = subprocess.run([
                    'sudo', 'cp', '-rf', f"{mount_point}/.", str(output_dir)
                ], capture_output=True, timeout=300)
                
                # Unmount
                subprocess.run(['sudo', 'umount', str(mount_point)], capture_output=True)
                
                # Fix permissions
                subprocess.run([
                    'sudo', 'chown', '-R', f"{os.getuid()}:{os.getgid()}", str(output_dir)
                ], capture_output=True)
                
                # Cleanup
                try:
                    mount_point.rmdir()
                except:
                    pass
                
                return copy_result.returncode == 0
            
            return False
            
        except:
            return False
    
    def _create_board_info(self, directory: Path, device_info: DeviceInfo):
        """Create board-info.txt file."""
        board_info_file = directory / "board-info.txt"
        
        board_info_lines = []
        
        # Add device information
        if device_info.baseband:
            board_info_lines.append(f"require version-baseband={device_info.baseband}")
        
        if device_info.bootloader:
            board_info_lines.append(f"require version-bootloader={device_info.bootloader}")
        
        if device_info.build_date:
            board_info_lines.append(f"require version-vendor={device_info.build_date}")
        
        # Look for additional board info in modem files
        modem_dir = directory / "modem"
        if modem_dir.exists():
            self._extract_modem_info(modem_dir, board_info_lines)
        
        # Write board info file
        if board_info_lines:
            try:
                board_info_file.write_text('\n'.join(sorted(set(board_info_lines))) + '\n')
                print_substep("Created", "board-info.txt")
            except Exception as e:
                print_warning(f"Failed to create board-info.txt: {e}")
    
    def _extract_modem_info(self, modem_dir: Path, board_info_lines: List[str]):
        """Extract modem information for board-info.txt."""
        import subprocess
        
        try:
            # Look for modem files and extract version strings
            for modem_file in modem_dir.rglob("*"):
                if modem_file.is_file():
                    try:
                        # Use strings command to extract version information
                        result = subprocess.run([
                            'strings', str(modem_file)
                        ], capture_output=True, text=True, timeout=30)
                        
                        if result.returncode == 0:
                            for line in result.stdout.splitlines():
                                if 'QC_IMAGE_VERSION_STRING=MPSS.' in line:
                                    version = line.replace('QC_IMAGE_VERSION_STRING=MPSS.', '').strip()
                                    if len(version) > 4:
                                        version = version[4:]  # Remove first 4 characters
                                    board_info_lines.append(f"require version-baseband={version}")
                                elif 'QC_IMAGE_VERSION_STRING' in line and 'MPSS' not in line:
                                    version_line = line.replace('QC_IMAGE_VERSION_STRING', 'require version-trustzone')
                                    board_info_lines.append(version_line)
                    except:
                        continue
        except:
            pass