"""
Validation utilities for DumprX.

Provides validation functions for URLs, file formats, tokens, and other inputs.
"""

import re
import mimetypes
from pathlib import Path
from typing import Optional, List, Union
from urllib.parse import urlparse


# Supported file extensions for firmware
FIRMWARE_EXTENSIONS = {
    '.zip', '.rar', '.7z', '.tar', '.tar.gz', '.tgz', '.tar.md5',
    '.ozip', '.ofp', '.ops', '.kdz', '.dz', '.exe',
    '.img', '.bin', '.dat', '.br', '.xz', '.pac',
    '.nb0', '.sin', '.ftf'
}

# Special firmware files
FIRMWARE_SPECIAL_FILES = {
    'system.new.dat', 'system.new.dat.br', 'system.new.dat.xz',
    'system.new.img', 'system.img', 'system-sign.img',
    'UPDATE.APP', 'payload.bin'
}

# URL patterns for supported services
URL_PATTERNS = {
    'mega': [
        r'https?://mega\.nz/',
        r'https?://mega\.co\.nz/',
    ],
    'mediafire': [
        r'https?://(?:www\.)?mediafire\.com/',
        r'https?://download\d*\.mediafire\.com/',
    ],
    'gdrive': [
        r'https?://drive\.google\.com/',
        r'https?://docs\.google\.com/.*?/drive/',
    ],
    'androidfilehost': [
        r'https?://(?:www\.)?androidfilehost\.com/',
        r'https?://(?:www\.)?afh\.io/',
    ],
    'onedrive': [
        r'https?://1drv\.ms/',
        r'https?://(?:.*\.)?sharepoint\.com/',
        r'https?://(?:.*\.)?live\.com/',
    ],
}


def validate_url(url: str) -> bool:
    """
    Validate if URL is properly formatted.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def detect_url_service(url: str) -> Optional[str]:
    """
    Detect which service a URL belongs to.
    
    Args:
        url: URL to check
        
    Returns:
        Service name or None if not supported
    """
    if not validate_url(url):
        return None
    
    for service, patterns in URL_PATTERNS.items():
        for pattern in patterns:
            if re.match(pattern, url, re.IGNORECASE):
                return service
    
    return None


def validate_supported_url(url: str) -> bool:
    """
    Check if URL is from a supported service.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is from supported service, False otherwise
    """
    return detect_url_service(url) is not None


def validate_file_format(file_path: Union[str, Path]) -> bool:
    """
    Check if file format is supported for firmware extraction.
    
    Args:
        file_path: Path to file or filename
        
    Returns:
        True if file format is supported, False otherwise
    """
    path = Path(file_path)
    filename = path.name.lower()
    
    # Check special firmware files
    if filename in FIRMWARE_SPECIAL_FILES:
        return True
    
    # Check by extension
    if path.suffix.lower() in FIRMWARE_EXTENSIONS:
        return True
    
    # Check compound extensions (.tar.gz, .tar.md5, etc.)
    if len(path.suffixes) >= 2:
        compound_ext = ''.join(path.suffixes[-2:]).lower()
        if compound_ext in FIRMWARE_EXTENSIONS:
            return True
    
    # Check for special patterns
    if re.search(r'ruu.*\.exe$', filename, re.IGNORECASE):
        return True
    
    if re.search(r'.*chunk.*', filename, re.IGNORECASE):
        return True
    
    if re.search(r'.*super.*\.img$', filename, re.IGNORECASE):
        return True
    
    if re.search(r'.*system.*\.sin$', filename, re.IGNORECASE):
        return True
    
    return False


def get_file_format_info(file_path: Union[str, Path]) -> dict:
    """
    Get detailed information about file format.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary with format information
    """
    path = Path(file_path)
    filename = path.name.lower()
    
    info = {
        'filename': path.name,
        'extension': path.suffix.lower(),
        'is_supported': validate_file_format(file_path),
        'format_type': 'unknown',
        'extraction_method': 'unknown'
    }
    
    # Determine format type and extraction method
    if filename in FIRMWARE_SPECIAL_FILES:
        if 'system.new.dat' in filename:
            info['format_type'] = 'android_sparse'
            info['extraction_method'] = 'sdat2img'
        elif filename == 'payload.bin':
            info['format_type'] = 'android_ota'
            info['extraction_method'] = 'payload_extractor'
        elif filename == 'UPDATE.APP':
            info['format_type'] = 'huawei_update'
            info['extraction_method'] = 'splituapp'
    
    elif path.suffix.lower() == '.kdz':
        info['format_type'] = 'lg_kdz'
        info['extraction_method'] = 'kdztools'
    
    elif path.suffix.lower() == '.ozip':
        info['format_type'] = 'oppo_ozip'
        info['extraction_method'] = 'ozipdecrypt'
    
    elif path.suffix.lower() in ['.ofp', '.ops']:
        info['format_type'] = 'oppo_firmware'
        info['extraction_method'] = 'oppo_decrypt'
    
    elif path.suffix.lower() == '.nb0':
        info['format_type'] = 'nokia_nb0'
        info['extraction_method'] = 'nb0_extract'
    
    elif path.suffix.lower() == '.pac':
        info['format_type'] = 'spreadtrum_pac'
        info['extraction_method'] = 'pacextractor'
    
    elif path.suffix.lower() == '.sin':
        info['format_type'] = 'sony_sin'
        info['extraction_method'] = 'unsin'
    
    elif re.search(r'ruu.*\.exe$', filename, re.IGNORECASE):
        info['format_type'] = 'htc_ruu'
        info['extraction_method'] = 'ruu_decrypt'
    
    elif path.suffix.lower() in ['.zip', '.rar', '.7z', '.tar']:
        info['format_type'] = 'archive'
        info['extraction_method'] = 'standard_archive'
    
    return info


def validate_token(token: str, token_type: str = 'github') -> bool:
    """
    Validate authentication token format.
    
    Args:
        token: Token to validate
        token_type: Type of token ('github', 'gitlab', 'telegram')
        
    Returns:
        True if token format is valid, False otherwise
    """
    if not token or not isinstance(token, str):
        return False
    
    token = token.strip()
    
    if token_type == 'github':
        # GitHub tokens start with 'ghp_', 'gho_', 'ghu_', 'ghs_', or 'ghr_'
        # and are 40 characters long (including prefix)
        return bool(re.match(r'^gh[pou]_[A-Za-z0-9]{36}$', token)) or \
               bool(re.match(r'^gh[sr]_[A-Za-z0-9_]{36,251}$', token))
    
    elif token_type == 'gitlab':
        # GitLab tokens are typically 20-26 characters, alphanumeric with dashes/underscores
        return bool(re.match(r'^[A-Za-z0-9_-]{20,26}$', token))
    
    elif token_type == 'telegram':
        # Telegram bot tokens have format: <bot_id>:<auth_token>
        # bot_id is numeric, auth_token is 35 characters alphanumeric/underscore/dash
        return bool(re.match(r'^\d+:[A-Za-z0-9_-]{35}$', token))
    
    return False


def validate_chat_id(chat_id: str) -> bool:
    """
    Validate Telegram chat ID format.
    
    Args:
        chat_id: Chat ID to validate
        
    Returns:
        True if chat ID format is valid, False otherwise
    """
    if not chat_id or not isinstance(chat_id, str):
        return False
    
    chat_id = chat_id.strip()
    
    # Chat ID can be:
    # - Positive integer (user ID)
    # - Negative integer (group/channel ID)
    # - String starting with @ (username)
    return bool(re.match(r'^-?\d+$', chat_id)) or \
           bool(re.match(r'^@[A-Za-z0-9_]{5,32}$', chat_id))


def validate_directory_path(path: Union[str, Path], must_exist: bool = False) -> bool:
    """
    Validate directory path.
    
    Args:
        path: Directory path to validate
        must_exist: Whether directory must already exist
        
    Returns:
        True if path is valid, False otherwise
    """
    try:
        path_obj = Path(path).resolve()
        
        if must_exist:
            return path_obj.exists() and path_obj.is_dir()
        else:
            # Check if parent directory exists (for creation)
            return path_obj.parent.exists()
    
    except Exception:
        return False


def validate_file_path(path: Union[str, Path], must_exist: bool = True) -> bool:
    """
    Validate file path.
    
    Args:
        path: File path to validate
        must_exist: Whether file must already exist
        
    Returns:
        True if path is valid, False otherwise
    """
    try:
        path_obj = Path(path).resolve()
        
        if must_exist:
            return path_obj.exists() and path_obj.is_file()
        else:
            # Check if parent directory exists (for creation)
            return path_obj.parent.exists()
    
    except Exception:
        return False


def get_supported_extensions() -> List[str]:
    """
    Get list of all supported file extensions.
    
    Returns:
        List of supported extensions
    """
    return sorted(list(FIRMWARE_EXTENSIONS))


def get_supported_services() -> List[str]:
    """
    Get list of all supported download services.
    
    Returns:
        List of supported services
    """
    return list(URL_PATTERNS.keys())