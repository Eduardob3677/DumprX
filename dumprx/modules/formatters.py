import re
from typing import Dict, Any

def format_device_name(brand: str, model: str, codename: str) -> str:
    """Format device name for display"""
    parts = []
    
    if brand and brand.lower() != 'unknown':
        parts.append(brand.title())
    
    if model and model.lower() != 'unknown':
        parts.append(model)
    
    if codename and codename.lower() != 'unknown':
        parts.append(f"({codename})")
    
    return ' '.join(parts) if parts else 'Unknown Device'

def format_android_version(version: str) -> str:
    """Format Android version for display"""
    if not version or version.lower() == 'unknown':
        return 'Unknown'
    
    # Map common version codes to names
    version_names = {
        '14': 'Android 14',
        '13': 'Android 13', 
        '12': 'Android 12',
        '11': 'Android 11',
        '10': 'Android 10',
        '9': 'Android 9 (Pie)',
        '8.1': 'Android 8.1 (Oreo)',
        '8.0': 'Android 8.0 (Oreo)',
        '7.1': 'Android 7.1 (Nougat)',
        '7.0': 'Android 7.0 (Nougat)',
        '6.0': 'Android 6.0 (Marshmallow)',
        '5.1': 'Android 5.1 (Lollipop)',
        '5.0': 'Android 5.0 (Lollipop)'
    }
    
    return version_names.get(version, f'Android {version}')

def format_build_fingerprint(fingerprint: str) -> str:
    """Format build fingerprint for better readability"""
    if not fingerprint:
        return 'Unknown'
    
    # Split fingerprint into components
    parts = fingerprint.split('/')
    if len(parts) >= 3:
        brand = parts[0]
        product = parts[1]
        version_info = parts[2] if len(parts) > 2 else ''
        
        return f"{brand}/{product}\n{version_info}"
    
    return fingerprint

def format_security_patch(patch: str) -> str:
    """Format security patch date"""
    if not patch or patch.lower() == 'unknown':
        return 'Unknown'
    
    # Try to format YYYY-MM-DD to readable format
    try:
        from datetime import datetime
        date_obj = datetime.strptime(patch, '%Y-%m-%d')
        return date_obj.strftime('%B %Y')
    except ValueError:
        return patch

def format_file_list(files: list, max_display: int = 20) -> str:
    """Format file list for display"""
    if not files:
        return "No files found"
    
    formatted_files = []
    
    for i, file_path in enumerate(files[:max_display]):
        if isinstance(file_path, dict):
            name = file_path.get('name', 'Unknown')
            size = file_path.get('size', 0)
            formatted_files.append(f"  {name} ({_format_size(size)})")
        else:
            formatted_files.append(f"  {file_path}")
    
    result = '\n'.join(formatted_files)
    
    if len(files) > max_display:
        result += f"\n  ... and {len(files) - max_display} more files"
    
    return result

def format_extraction_summary(summary: Dict[str, Any]) -> str:
    """Format extraction summary for display"""
    lines = []
    
    if 'total_files' in summary:
        lines.append(f"Total files extracted: {summary['total_files']}")
    
    if 'partitions' in summary:
        lines.append(f"Partitions processed: {len(summary['partitions'])}")
        for partition in summary['partitions']:
            lines.append(f"  - {partition}")
    
    if 'size_extracted' in summary:
        lines.append(f"Total size: {_format_size(summary['size_extracted'])}")
    
    if 'warnings' in summary and summary['warnings']:
        lines.append(f"Warnings: {len(summary['warnings'])}")
        for warning in summary['warnings'][:5]:  # Show first 5 warnings
            lines.append(f"  - {warning}")
    
    return '\n'.join(lines)

def format_git_summary(repo_info: Dict[str, Any]) -> str:
    """Format Git repository summary"""
    lines = []
    
    if 'repository' in repo_info:
        lines.append(f"Repository: {repo_info['repository']}")
    
    if 'branch' in repo_info:
        lines.append(f"Branch: {repo_info['branch']}")
    
    if 'commits' in repo_info:
        lines.append(f"Commits: {repo_info['commits']}")
    
    if 'url' in repo_info:
        lines.append(f"URL: {repo_info['url']}")
    
    return '\n'.join(lines)

def format_progress_bar(current: int, total: int, width: int = 40) -> str:
    """Create a simple ASCII progress bar"""
    if total == 0:
        return "[" + "?" * width + "]"
    
    progress = current / total
    filled_width = int(width * progress)
    
    bar = "█" * filled_width + "░" * (width - filled_width)
    percentage = f"{progress * 100:.1f}%"
    
    return f"[{bar}] {percentage}"

def _format_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text with ellipsis if too long"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."

def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace and invalid characters"""
    if not text:
        return ""
    
    # Remove control characters except newlines and tabs
    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Normalize whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    return cleaned.strip()