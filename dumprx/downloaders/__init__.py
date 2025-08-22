"""Downloaders package for various file hosting services."""

from dumprxbase import BaseDownloader, DownloadResult
from dumprxmega import MegaDownloader
from dumprxmediafire import MediaFireDownloader
from dumprxgdrive import GDriveDownloader
from dumprxandroidfilehost import AndroidFileHostDownloader

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
    from dumprxmodules.validator import detect_url_service
    
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