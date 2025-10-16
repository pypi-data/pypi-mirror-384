"""
Media Crawler - A robust, extensible web crawler for downloading media content.

This package provides a complete solution for crawling and downloading media
from various platforms like YouTube and SoundCloud.
"""

__version__ = "1.0.3"
__author__ = "Media Crawler Team"

# Import main classes for easy access
from .config import (
    ApplicationConfig,
    CrawlerConfig,
    DatabaseConfig,
    DownloadConfig,
    SeleniumConfig,
    PlatformConfig
)
from .crawler import Crawler
from .factory import CrawlerFactory
from .exceptions import (
    CrawlerException,
    ConfigurationException,
    DatabaseException,
    DownloadException,
    NetworkException
)

__all__ = [
    # Main classes
    'Crawler',
    'CrawlerFactory',
    
    # Configuration
    'ApplicationConfig',
    'CrawlerConfig',
    'DatabaseConfig',
    'DownloadConfig',
    'SeleniumConfig',
    'PlatformConfig',
    
    # Exceptions
    'CrawlerException',
    'ConfigurationException',
    'DatabaseException',
    'DownloadException',
    'NetworkException',
    
    # Version
    '__version__',
]
