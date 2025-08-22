"""
File handling utilities for DumprX.

Provides file operations, directory management, and file system utilities.
"""

import os
import shutil
import hashlib
import mimetypes
from pathlib import Path
from typing import List, Dict, Optional, Union, Iterator
from dataclasses import dataclass

from ..modules.formatter import format_file_size, sanitize_filename, sanitize_path


@dataclass
class FileInfo:
    """Information about a file."""
    path: Path
    size: int
    mime_type: Optional[str] = None
    md5_hash: Optional[str] = None
    is_executable: bool = False
    is_archive: bool = False


class FileHandler:
    """File and directory operations handler."""
    
    def __init__(self, base_path: Union[str, Path]):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def ensure_directory(self, directory: Union[str, Path]) -> Path:
        """
        Ensure directory exists, create if necessary.
        
        Args:
            directory: Directory path
            
        Returns:
            Path object of the directory
        """
        dir_path = Path(directory)
        if not dir_path.is_absolute():
            dir_path = self.base_path / dir_path
        
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    
    def clean_directory(self, directory: Union[str, Path], keep_hidden: bool = True) -> int:
        """
        Clean directory contents.
        
        Args:
            directory: Directory to clean
            keep_hidden: Whether to keep hidden files/directories
            
        Returns:
            Number of items removed
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return 0
        
        items_removed = 0
        
        for item in dir_path.iterdir():
            if keep_hidden and item.name.startswith('.'):
                continue
            
            try:
                if item.is_file():
                    item.unlink()
                    items_removed += 1
                elif item.is_dir():
                    shutil.rmtree(item)
                    items_removed += 1
            except Exception:
                # Skip files that can't be removed
                continue
        
        return items_removed
    
    def copy_file(self, source: Union[str, Path], destination: Union[str, Path], 
                  preserve_metadata: bool = True) -> bool:
        """
        Copy file with error handling.
        
        Args:
            source: Source file path
            destination: Destination file path
            preserve_metadata: Whether to preserve file metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            # Ensure destination directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            if preserve_metadata:
                shutil.copy2(source_path, dest_path)
            else:
                shutil.copy(source_path, dest_path)
            
            return True
            
        except Exception:
            return False
    
    def move_file(self, source: Union[str, Path], destination: Union[str, Path]) -> bool:
        """
        Move file with error handling.
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            source_path = Path(source)
            dest_path = Path(destination)
            
            # Ensure destination directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.move(str(source_path), str(dest_path))
            return True
            
        except Exception:
            return False
    
    def safe_remove(self, path: Union[str, Path]) -> bool:
        """
        Safely remove file or directory.
        
        Args:
            path: Path to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            path_obj = Path(path)
            
            if path_obj.is_file():
                path_obj.unlink()
            elif path_obj.is_dir():
                shutil.rmtree(path_obj)
            
            return True
            
        except Exception:
            return False
    
    def get_file_info(self, file_path: Union[str, Path], calculate_hash: bool = False) -> FileInfo:
        """
        Get detailed file information.
        
        Args:
            file_path: Path to file
            calculate_hash: Whether to calculate MD5 hash
            
        Returns:
            FileInfo object with file details
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        stat = path.stat()
        size = stat.st_size
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(path))
        
        # Check if executable
        is_executable = os.access(path, os.X_OK)
        
        # Check if archive based on extension
        archive_extensions = {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'}
        is_archive = path.suffix.lower() in archive_extensions
        
        # Calculate hash if requested
        md5_hash = None
        if calculate_hash:
            md5_hash = self.calculate_md5(path)
        
        return FileInfo(
            path=path,
            size=size,
            mime_type=mime_type,
            md5_hash=md5_hash,
            is_executable=is_executable,
            is_archive=is_archive
        )
    
    def calculate_md5(self, file_path: Union[str, Path], chunk_size: int = 8192) -> str:
        """
        Calculate MD5 hash of file.
        
        Args:
            file_path: Path to file
            chunk_size: Size of chunks to read
            
        Returns:
            MD5 hash as hexadecimal string
        """
        md5_hash = hashlib.md5()
        
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                md5_hash.update(chunk)
        
        return md5_hash.hexdigest()
    
    def find_files(self, directory: Union[str, Path], pattern: str = "*", 
                   recursive: bool = True) -> List[Path]:
        """
        Find files matching pattern.
        
        Args:
            directory: Directory to search
            pattern: File pattern (glob)
            recursive: Whether to search recursively
            
        Returns:
            List of matching file paths
        """
        dir_path = Path(directory)
        
        if recursive:
            return list(dir_path.rglob(pattern))
        else:
            return list(dir_path.glob(pattern))
    
    def find_by_extension(self, directory: Union[str, Path], 
                         extensions: List[str], recursive: bool = True) -> List[Path]:
        """
        Find files by extensions.
        
        Args:
            directory: Directory to search
            extensions: List of extensions (with or without dots)
            recursive: Whether to search recursively
            
        Returns:
            List of matching file paths
        """
        # Normalize extensions
        normalized_extensions = []
        for ext in extensions:
            if not ext.startswith('.'):
                ext = '.' + ext
            normalized_extensions.append(ext.lower())
        
        dir_path = Path(directory)
        matching_files = []
        
        search_func = dir_path.rglob if recursive else dir_path.glob
        
        for file_path in search_func("*"):
            if file_path.is_file() and file_path.suffix.lower() in normalized_extensions:
                matching_files.append(file_path)
        
        return matching_files
    
    def get_directory_size(self, directory: Union[str, Path]) -> int:
        """
        Calculate total size of directory.
        
        Args:
            directory: Directory path
            
        Returns:
            Total size in bytes
        """
        total_size = 0
        dir_path = Path(directory)
        
        for file_path in dir_path.rglob("*"):
            if file_path.is_file():
                try:
                    total_size += file_path.stat().st_size
                except:
                    # Skip files that can't be accessed
                    continue
        
        return total_size
    
    def create_directory_structure(self, structure: Dict[str, any], 
                                 base_dir: Union[str, Path]) -> List[Path]:
        """
        Create directory structure from dictionary.
        
        Args:
            structure: Dictionary defining directory structure
            base_dir: Base directory to create structure in
            
        Returns:
            List of created paths
        """
        created_paths = []
        base_path = Path(base_dir)
        
        def create_recursive(current_structure: Dict, current_path: Path):
            for name, content in current_structure.items():
                item_path = current_path / sanitize_filename(name)
                
                if isinstance(content, dict):
                    # Directory
                    item_path.mkdir(parents=True, exist_ok=True)
                    created_paths.append(item_path)
                    create_recursive(content, item_path)
                else:
                    # File
                    item_path.parent.mkdir(parents=True, exist_ok=True)
                    if isinstance(content, str):
                        item_path.write_text(content, encoding='utf-8')
                    elif isinstance(content, bytes):
                        item_path.write_bytes(content)
                    created_paths.append(item_path)
        
        create_recursive(structure, base_path)
        return created_paths
    
    def backup_file(self, file_path: Union[str, Path], backup_suffix: str = ".bak") -> Path:
        """
        Create backup of file.
        
        Args:
            file_path: File to backup
            backup_suffix: Suffix for backup file
            
        Returns:
            Path to backup file
        """
        source_path = Path(file_path)
        backup_path = source_path.with_suffix(source_path.suffix + backup_suffix)
        
        # If backup already exists, add number
        counter = 1
        while backup_path.exists():
            backup_path = source_path.with_suffix(f"{source_path.suffix}{backup_suffix}.{counter}")
            counter += 1
        
        shutil.copy2(source_path, backup_path)
        return backup_path
    
    def list_directory_contents(self, directory: Union[str, Path], 
                              include_hidden: bool = False) -> List[Dict[str, any]]:
        """
        List directory contents with details.
        
        Args:
            directory: Directory to list
            include_hidden: Whether to include hidden files
            
        Returns:
            List of file/directory information
        """
        dir_path = Path(directory)
        contents = []
        
        for item in dir_path.iterdir():
            if not include_hidden and item.name.startswith('.'):
                continue
            
            item_info = {
                'name': item.name,
                'path': str(item),
                'is_file': item.is_file(),
                'is_dir': item.is_dir(),
                'size': 0,
                'size_formatted': '0 B'
            }
            
            if item.is_file():
                try:
                    size = item.stat().st_size
                    item_info['size'] = size
                    item_info['size_formatted'] = format_file_size(size)
                except:
                    pass
            elif item.is_dir():
                try:
                    size = self.get_directory_size(item)
                    item_info['size'] = size
                    item_info['size_formatted'] = format_file_size(size)
                except:
                    pass
            
            contents.append(item_info)
        
        return sorted(contents, key=lambda x: (not x['is_dir'], x['name'].lower()))
    
    def is_empty_directory(self, directory: Union[str, Path]) -> bool:
        """
        Check if directory is empty.
        
        Args:
            directory: Directory to check
            
        Returns:
            True if directory is empty, False otherwise
        """
        dir_path = Path(directory)
        
        if not dir_path.exists() or not dir_path.is_dir():
            return False
        
        try:
            next(dir_path.iterdir())
            return False
        except StopIteration:
            return True
    
    def get_unique_filename(self, file_path: Union[str, Path]) -> Path:
        """
        Get unique filename by adding number suffix if file exists.
        
        Args:
            file_path: Desired file path
            
        Returns:
            Unique file path
        """
        path = Path(file_path)
        
        if not path.exists():
            return path
        
        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        
        counter = 1
        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1