"""
Download manager for handling track/video downloads with strategy pattern.
"""
import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Any
from yt_dlp import YoutubeDL
from urllib.error import HTTPError
import urllib3

from .config import DownloadConfig, CrawlerConfig
from .utils import retry

logger = logging.getLogger(__name__)


class IDownloadStrategy(ABC):
    """Interface for download strategies."""
    
    @abstractmethod
    def download(self, url: str, index: int, total: int) -> Optional[Tuple[str, str]]:
        """
        Download a track/video.
        
        Args:
            url: URL to download
            index: Current index (for logging)
            total: Total number of items (for logging)
            
        Returns:
            Tuple of (url, title) if successful, None otherwise
        """
        pass


class YtDlpDownloadStrategy(IDownloadStrategy):
    """Download strategy using yt-dlp."""
    
    def __init__(self, download_config: DownloadConfig, crawler_config: CrawlerConfig):
        """
        Initialize yt-dlp download strategy.
        
        Args:
            download_config: Download configuration
            crawler_config: Crawler configuration for retry settings
        """
        self.download_config = download_config
        self.crawler_config = crawler_config
    
    def _get_info_options(self) -> dict[str, Any]:
        """Get yt-dlp options for info extraction."""
        return {
            'quiet': self.download_config.quiet,
            'no_warnings': self.download_config.no_warnings,
            'nocheckcertificate': self.download_config.nocheckcertificate,
        }
    
    def _get_download_options(self) -> dict[str, Any]:
        """Get yt-dlp options for downloading."""
        return {
            'format': self.download_config.format,
            'outtmpl': os.path.join(
                self.download_config.download_folder,
                '%(title)s.%(ext)s'
            ),
            'quiet': self.download_config.quiet,
            'no_warnings': self.download_config.no_warnings,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': self.download_config.audio_format,
                'preferredquality': self.download_config.audio_quality,
            }],
            'nocheckcertificate': self.download_config.nocheckcertificate,
            'user-agent': self.download_config.user_agent,
        }
    
    @retry(
        max_attempts=3,
        backoff_base=2,
        exceptions=(HTTPError, urllib3.exceptions.HTTPError, Exception)
    )
    def _extract_info(self, ydl: YoutubeDL, url: str) -> Optional[Any]:
        """Extract video/track information with retry."""
        try:
            return ydl.extract_info(url, download=False)  # type: ignore
        except HTTPError as e:
            if e.code == 404:
                logger.warning(f"HTTP 404 Not Found for {url}, skipping")
                return None
            raise
    
    @retry(
        max_attempts=3,
        backoff_base=2,
        exceptions=(urllib3.exceptions.HTTPError, Exception)
    )
    def _download_track(self, ydl: YoutubeDL, url: str) -> bool:
        """Download track with retry."""
        ydl.download([url])
        return True
    
    def download(self, url: str, index: int, total: int) -> Optional[Tuple[str, str]]:
        """
        Download a track using yt-dlp.
        
        Args:
            url: URL to download
            index: Current index
            total: Total number of items
            
        Returns:
            Tuple of (url, title) if successful, None otherwise
        """
        logger.debug(f"[{index}/{total}] Processing: {url}")
        
        # Extract info first
        try:
            with YoutubeDL(self._get_info_options()) as ydl:  # type: ignore
                info = self._extract_info(ydl, url)
                if not info:
                    logger.debug(f"[{index}/{total}] Could not get info, skipping {url}")
                    return None
                
                title = info.get('title')
                if not title:
                    logger.debug(f"[{index}/{total}] Could not get title, skipping {url}")
                    return None
        except Exception as e:
            logger.debug(f"[{index}/{total}] Failed to fetch info for {url}: {e}")
            return None
        
        # Check if file already exists
        filename = os.path.join(
            self.download_config.download_folder,
            f"{title}.{self.download_config.audio_format}"
        )
        if os.path.exists(filename):
            logger.debug(f"[{index}/{total}] File exists, skipping download: {filename}")
            return url, title
        
        # Download the track
        try:
            with YoutubeDL(self._get_download_options()) as ydl:  # type: ignore
                success = self._download_track(ydl, url)
                if success:
                    logger.debug(f"[{index}/{total}] Finished: {title}")
                    return url, title
                else:
                    logger.warning(f"[{index}/{total}] Failed to download {url} after retries")
                    return None
        except Exception as e:
            logger.warning(f"[{index}/{total}] Failed to download {url}: {e}")
            return None


class DownloadManager:
    """Manager for handling downloads with pluggable strategies."""
    
    def __init__(self, strategy: IDownloadStrategy):
        """
        Initialize download manager.
        
        Args:
            strategy: Download strategy to use
        """
        self.strategy = strategy
    
    def download(self, url: str, index: int = 1, total: int = 1) -> Optional[Tuple[str, str]]:
        """
        Download using the configured strategy.
        
        Args:
            url: URL to download
            index: Current index (for logging)
            total: Total number of items (for logging)
            
        Returns:
            Tuple of (url, title) if successful, None otherwise
        """
        return self.strategy.download(url, index, total)
    
    def set_strategy(self, strategy: IDownloadStrategy) -> None:
        """
        Change the download strategy.
        
        Args:
            strategy: New download strategy
        """
        self.strategy = strategy


class DownloadManagerFactory:
    """Factory for creating download manager instances."""
    
    @staticmethod
    def create_manager(
        download_config: DownloadConfig,
        crawler_config: CrawlerConfig,
        strategy_type: str = "ytdlp"
    ) -> DownloadManager:
        """
        Create a download manager with the specified strategy.
        
        Args:
            download_config: Download configuration
            crawler_config: Crawler configuration
            strategy_type: Type of strategy (currently only 'ytdlp' supported)
            
        Returns:
            Download manager instance
            
        Raises:
            ValueError: If strategy type is not supported
        """
        if strategy_type.lower() == "ytdlp":
            strategy = YtDlpDownloadStrategy(download_config, crawler_config)
            return DownloadManager(strategy)
        else:
            raise ValueError(f"Unsupported download strategy: {strategy_type}")
