import os
import shutil
import hashlib
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import urlparse


def get_file_extension(filepath: str) -> str:
    return Path(filepath).suffix.lower()


def get_file_type(filepath: str) -> str:
    path = Path(filepath)
    name = path.name.lower()
    
    if any(pattern in name for pattern in [".zip", ".rar", ".7z", ".tar"]):
        return "archive"
    elif any(pattern in name for pattern in [".ozip", ".ofp", ".ops"]):
        return "encrypted_firmware"
    elif name.endswith(".kdz"):
        return "lg_kdz"
    elif name.startswith("ruu_") and name.endswith(".exe"):
        return "htc_ruu"
    elif "system.new.dat" in name:
        return "android_dat"
    elif any(pattern in name for pattern in ["system.img", "system-sign.img"]):
        return "system_image"
    elif name == "update.app":
        return "huawei_update"
    elif name.endswith(".emmc.img") or name.endswith(".img.ext4"):
        return "emmc_image"
    elif name.endswith(".nb0"):
        return "nokia_nb0"
    elif "chunk" in name:
        return "sparse_chunk"
    elif name.endswith(".pac"):
        return "spreadtrum_pac"
    elif "super" in name and name.endswith(".img"):
        return "super_image"
    elif "system" in name and name.endswith(".sin"):
        return "sony_sin"
    elif name == "payload.bin":
        return "ota_payload"
    else:
        return "unknown"


def is_url(string: str) -> bool:
    try:
        result = urlparse(string)
        return all([result.scheme, result.netloc])
    except:
        return False


def calculate_sha1(filepath: Path) -> str:
    hash_sha1 = hashlib.sha1()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha1.update(chunk)
    return hash_sha1.hexdigest()


def safe_move(src: Path, dst: Path) -> bool:
    try:
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            return True
        return False
    except Exception:
        return False


def safe_copy(src: Path, dst: Path) -> bool:
    try:
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dst))
            return True
        return False
    except Exception:
        return False


def run_command(cmd: List[str], cwd: Optional[Path] = None, capture_output: bool = True) -> Tuple[bool, str]:
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd, 
            capture_output=capture_output,
            text=True,
            check=True
        )
        return True, result.stdout if capture_output else ""
    except subprocess.CalledProcessError as e:
        return False, e.stderr if capture_output else str(e)
    except Exception as e:
        return False, str(e)


def extract_with_7z(archive_path: Path, extract_to: Path, tool_path: Path) -> bool:
    success, _ = run_command([
        str(tool_path), "x", "-y", str(archive_path), f"-o{extract_to}"
    ])
    return success


def find_files_by_pattern(directory: Path, patterns: List[str]) -> List[Path]:
    found_files = []
    for pattern in patterns:
        found_files.extend(directory.glob(pattern))
    return found_files


def clean_filename(filename: str) -> str:
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()


def get_file_size(filepath: Path) -> int:
    try:
        return filepath.stat().st_size
    except:
        return 0


def create_directory_structure(base_path: Path, subdirs: List[str]) -> None:
    for subdir in subdirs:
        (base_path / subdir).mkdir(parents=True, exist_ok=True)