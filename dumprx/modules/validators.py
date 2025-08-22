import re
import os
from pathlib import Path
from typing import Union

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe filesystem usage"""
    # Remove invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Trim dots and spaces from start/end
    sanitized = sanitized.strip('. ')
    
    # Ensure it's not empty
    if not sanitized:
        sanitized = "unnamed_file"
    
    return sanitized

def sanitize_path(path: str) -> str:
    """Sanitize full path"""
    parts = Path(path).parts
    sanitized_parts = [sanitize_filename(part) for part in parts]
    return str(Path(*sanitized_parts))

def validate_url(url: str) -> bool:
    """Validate URL format"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_pattern.match(url) is not None

def validate_file_path(file_path: Union[str, Path]) -> bool:
    """Validate file path exists and is readable"""
    path = Path(file_path)
    return path.exists() and path.is_file() and os.access(path, os.R_OK)

def validate_directory_path(dir_path: Union[str, Path]) -> bool:
    """Validate directory path exists and is readable"""
    path = Path(dir_path)
    return path.exists() and path.is_dir() and os.access(path, os.R_OK)

def is_supported_archive(filename: str) -> bool:
    """Check if file is a supported archive format"""
    supported_extensions = {
        '.zip', '.rar', '.7z', '.tar', '.gz', '.tgz', '.tar.gz', '.tar.md5'
    }
    
    filename_lower = filename.lower()
    
    # Check for exact extensions
    for ext in supported_extensions:
        if filename_lower.endswith(ext):
            return True
    
    return False

def is_supported_firmware(filename: str) -> bool:
    """Check if file is a supported firmware format"""
    filename_lower = filename.lower()
    
    firmware_patterns = [
        r'\.ozip$', r'\.ofp$', r'\.ops$', r'\.kdz$', r'\.dz$',
        r'\.nb0$', r'\.pac$', r'\.img$', r'\.bin$', r'\.dat$',
        r'system\.new\.dat', r'system\.new\.img', r'system\.img',
        r'system-sign\.img', r'update\.app$', r'payload\.bin$',
        r'\.emmc\.img$', r'\.img\.ext4$', r'system\.bin$',
        r'system-p$', r'.*chunk.*', r'.*super.*\.img$',
        r'.*system.*\.sin$', r'ruu_.*\.exe$'
    ]
    
    for pattern in firmware_patterns:
        if re.search(pattern, filename_lower):
            return True
    
    return False

def is_url(text: str) -> bool:
    """Check if text is a URL"""
    return text.startswith(('http://', 'https://', 'ftp://'))

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def extract_filename_from_url(url: str) -> str:
    """Extract filename from URL"""
    from urllib.parse import urlparse, unquote
    
    parsed_url = urlparse(url)
    filename = os.path.basename(unquote(parsed_url.path))
    
    if not filename or filename == '/':
        filename = "downloaded_file"
    
    return sanitize_filename(filename)