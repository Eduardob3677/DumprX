"""
DumprX - Modern Python Firmware Dumper

A professional firmware extraction and analysis toolkit with modern CLI interface.
Migrated from bash to Python with improved architecture and functionality.
"""

__version__ = "2.0.0"
__author__ = "DumprX Team"
__description__ = "Professional firmware extraction and analysis toolkit"

# Core module imports
from .core.config import Config
from .core.device_info import DeviceInfo

__all__ = ["Config", "DeviceInfo", "__version__"]