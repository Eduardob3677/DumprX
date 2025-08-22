"""
Formatting utilities for DumprX.

Provides text formatting, file size formatting, and sanitization functions.
"""

import re
import unicodedata
from typing import Optional, Union
from pathlib import Path

from ..core.device_info import DeviceInfo


def format_device_info(device_info: DeviceInfo) -> str:
    """
    Format device information for display.
    
    Args:
        device_info: DeviceInfo instance
        
    Returns:
        Formatted device information string
    """
    lines = []
    
    if device_info.brand or device_info.model:
        name_parts = []
        if device_info.brand:
            name_parts.append(device_info.brand)
        if device_info.model:
            name_parts.append(device_info.model)
        lines.append(f"Device: {' '.join(name_parts)}")
    
    if device_info.device:
        lines.append(f"Codename: {device_info.device}")
    
    if device_info.release:
        lines.append(f"Android Version: {device_info.release}")
    
    if device_info.build_id:
        lines.append(f"Build ID: {device_info.build_id}")
    
    if device_info.flavor:
        lines.append(f"Build Flavor: {device_info.flavor}")
    
    if device_info.platform:
        lines.append(f"Platform: {device_info.platform}")
    
    if device_info.security_patch:
        lines.append(f"Security Patch: {device_info.security_patch}")
    
    if device_info.fingerprint:
        lines.append(f"Fingerprint: {device_info.fingerprint}")
    
    return "\n".join(lines) if lines else "No device information available"


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Formatted size string (e.g., "1.5 GB")
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    if i == 0:
        return f"{int(size)} {size_names[i]}"
    else:
        return f"{size:.1f} {size_names[i]}"


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """
    Sanitize filename for filesystem compatibility.
    
    Args:
        filename: Original filename
        replacement: Character to replace invalid characters with
        
    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(invalid_chars, replacement, filename)
    
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip(' .')
    
    # Handle reserved names on Windows
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    name_part = sanitized.split('.')[0].upper()
    if name_part in reserved_names:
        sanitized = f"{replacement}{sanitized}"
    
    # Limit length
    if len(sanitized) > 255:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        max_name_len = 255 - len(ext) - 1 if ext else 255
        sanitized = f"{name[:max_name_len]}.{ext}" if ext else name[:255]
    
    # Ensure not empty
    if not sanitized:
        sanitized = "unnamed"
    
    return sanitized


def sanitize_path(path: Union[str, Path], replacement: str = "_") -> Path:
    """
    Sanitize all components of a path.
    
    Args:
        path: Original path
        replacement: Character to replace invalid characters with
        
    Returns:
        Sanitized Path object
    """
    path_obj = Path(path)
    
    # Sanitize each part of the path
    sanitized_parts = []
    for part in path_obj.parts:
        if part in ('/', '\\', '..'):
            # Keep root and parent directory references
            sanitized_parts.append(part)
        else:
            sanitized_parts.append(sanitize_filename(part, replacement))
    
    return Path(*sanitized_parts) if sanitized_parts else Path(".")


def format_progress_bar(current: int, total: int, width: int = 50) -> str:
    """
    Create a simple ASCII progress bar.
    
    Args:
        current: Current progress value
        total: Total progress value
        width: Width of progress bar in characters
        
    Returns:
        Formatted progress bar string
    """
    if total == 0:
        percentage = 100
    else:
        percentage = min(100, int((current / total) * 100))
    
    filled_width = int((percentage / 100) * width)
    bar = "█" * filled_width + "░" * (width - filled_width)
    
    return f"[{bar}] {percentage}%"


def truncate_text(text: str, max_length: int = 80, suffix: str = "...") -> str:
    """
    Truncate text to specified length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to append when truncating
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    truncate_length = max_length - len(suffix)
    return text[:truncate_length] + suffix


def normalize_text(text: str) -> str:
    """
    Normalize text by removing accents and converting to ASCII.
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text
    """
    # Normalize unicode characters
    normalized = unicodedata.normalize('NFKD', text)
    
    # Remove non-ASCII characters
    ascii_text = normalized.encode('ascii', 'ignore').decode('ascii')
    
    return ascii_text


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        return f"{hours}h {remaining_minutes}m"


def format_table_row(columns: list, widths: list, separator: str = " | ") -> str:
    """
    Format a table row with specified column widths.
    
    Args:
        columns: List of column values
        widths: List of column widths
        separator: Column separator
        
    Returns:
        Formatted table row
    """
    formatted_columns = []
    
    for i, (column, width) in enumerate(zip(columns, widths)):
        column_str = str(column)
        if len(column_str) > width:
            column_str = truncate_text(column_str, width)
        else:
            column_str = column_str.ljust(width)
        formatted_columns.append(column_str)
    
    return separator.join(formatted_columns)