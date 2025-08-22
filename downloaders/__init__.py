"""Downloaders package for various file hosting services."""

from .base import BaseDownloader, DownloadResult
from .mega import MegaDownloader
from .mediafire import MediaFireDownloader
from .gdrive import GDriveDownloader
from .androidfilehost import AndroidFileHostDownloader

# Downloader registry
DOWNLOADERS = {
    'mega': MegaDownloader,
    'mediafire': MediaFireDownloader,
    'gdrive': GDriveDownloader,
    'androidfilehost': AndroidFileHostDownloader,
}


def get_downloader(url: str, service: str = 'auto') -> BaseDownloader:
    """
    Get appropriate downloader for URL.
    
    Args:
        url: URL to download from
        service: Service name or 'auto' for auto-detection
        
    Returns:
        Downloader instance or None if not supported
    """
    from ..modules.validator import detect_url_service
    
    if service == 'auto':
        service = detect_url_service(url)
    
    if service and service in DOWNLOADERS:
        return DOWNLOADERS[service]()
    
    return None


__all__ = [
    'BaseDownloader',
    'DownloadResult', 
    'MegaDownloader',
    'MediaFireDownloader',
    'GDriveDownloader',
    'AndroidFileHostDownloader',
    'get_downloader'
]