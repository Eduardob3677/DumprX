"""Extractors package for various firmware formats."""

from dumprxbase import BaseExtractor, ExtractionResult
from dumprxarchive import ArchiveExtractor
from dumprxandroid import AndroidExtractor
from dumprxlg_kdz import LGKDZExtractor

# Extractor registry
EXTRACTORS = {
    'archive': ArchiveExtractor,
    'android_sparse': AndroidExtractor,
    'android_ota': AndroidExtractor,
    'lg_kdz': LGKDZExtractor,
    'huawei_update': AndroidExtractor,
}


def get_extractor(file_path: str, format_type: str = 'auto') -> BaseExtractor:
    """
    Get appropriate extractor for file.
    
    Args:
        file_path: Path to file to extract
        format_type: Format type or 'auto' for auto-detection
        
    Returns:
        Extractor instance or None if not supported
    """
    from dumprxmodules.validator import get_file_format_info
    
    if format_type == 'auto':
        format_info = get_file_format_info(file_path)
        format_type = format_info['format_type']
    
    if format_type and format_type in EXTRACTORS:
        return EXTRACTORS[format_type]()
    
    # Default to archive extractor for standard archives
    if format_type in ['unknown', 'archive']:
        return ArchiveExtractor()
    
    return None


__all__ = [
    'BaseExtractor',
    'ExtractionResult',
    'ArchiveExtractor', 
    'AndroidExtractor',
    'LGKDZExtractor',
    'get_extractor'
]