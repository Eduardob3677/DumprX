#!/usr/bin/env python3

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Union

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

console = Console()

def get_project_dir() -> Path:
    return Path(__file__).parent.parent.absolute()

def ensure_directories(*dirs: Union[str, Path]) -> None:
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

def cleanup_directory(dir_path: Union[str, Path]) -> None:
    if Path(dir_path).exists():
        shutil.rmtree(dir_path)

def run_command(cmd: List[str], cwd: Optional[Path] = None, capture_output: bool = True, 
                check: bool = True) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=capture_output, 
                            text=True, check=check)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Command failed: {' '.join(cmd)}[/red]")
        console.print(f"[red]Error: {e.stderr}[/red]")
        raise

def check_command_exists(command: str) -> bool:
    return shutil.which(command) is not None

def get_file_extension(filepath: Union[str, Path]) -> str:
    return Path(filepath).suffix.lstrip('.')

def get_filename_without_ext(filepath: Union[str, Path]) -> str:
    return Path(filepath).stem

def find_files_by_pattern(directory: Union[str, Path], pattern: str) -> List[Path]:
    return list(Path(directory).glob(pattern))

def copy_file_or_dir(src: Union[str, Path], dst: Union[str, Path]) -> None:
    src_path = Path(src)
    dst_path = Path(dst)
    
    if src_path.is_file():
        shutil.copy2(src_path, dst_path)
    elif src_path.is_dir():
        shutil.copytree(src_path, dst_path, dirs_exist_ok=True)

def move_file_or_dir(src: Union[str, Path], dst: Union[str, Path]) -> None:
    shutil.move(str(src), str(dst))

def get_file_size(filepath: Union[str, Path]) -> int:
    return Path(filepath).stat().st_size

def is_file_larger_than(filepath: Union[str, Path], size_mb: int) -> bool:
    return get_file_size(filepath) > size_mb * 1024 * 1024

class ProgressManager:
    def __init__(self):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        )
    
    def __enter__(self):
        self.progress.start()
        return self.progress
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.progress.stop()