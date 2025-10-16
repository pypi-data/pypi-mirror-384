"""
Factory module for creating and configuring crawler instances.
"""
import logging
from typing import List, Optional

from .config import ApplicationConfig, CrawlerConfig
from .database import DatabaseFactory
from .webdriver import WebDriverFactory
from .downloader import DownloadManagerFactory
from .link_extractor import LinkExtractorFactory
from .state_manager import StateManager
from .crawler import Crawler
from .utils import url_to_filename

logger = logging.getLogger(__name__)


class CrawlerFactory:
    """Factory for creating fully configured crawler instances."""
    
    @staticmethod
    def create_crawler(
        config: ApplicationConfig,
        start_urls: Optional[List[str]] = None,
        state_file_name: Optional[str] = None,
        quiet: bool = False
    ) -> Crawler:
        """
        Create a fully configured crawler instance.
        
        Args:
            config: Application configuration
            start_urls: Initial URLs to crawl
            state_file_name: Ignored (kept for compatibility, no longer used)
            quiet: If True, use minimal progress display
            
        Returns:
            Configured crawler instance
        """
        # Create all components
        if not quiet:
            logger.info("Creating database...")
        database = DatabaseFactory.create_database(config.database)
        
        if not quiet:
            logger.info("Creating web driver (this may take a moment)...")
        webdriver = WebDriverFactory.create_driver(config.selenium, config.crawler)
        
        if not quiet:
            logger.info("Creating download manager...")
        download_manager = DownloadManagerFactory.create_manager(
            config.download,
            config.crawler
        )
        
        if not quiet:
            logger.info("Creating link extractor...")
        link_extractor = LinkExtractorFactory.create_extractor(
            config.platform,
            database
        )
        
        if not quiet:
            logger.info("Creating state manager...")
        state_manager = StateManager()  # No file path needed anymore
        
        # Create and return crawler
        crawler = Crawler(
            config=config,
            database=database,
            webdriver=webdriver,
            download_manager=download_manager,
            link_extractor=link_extractor,
            state_manager=state_manager,
            start_urls=start_urls or [],
            quiet=quiet
        )
        
        if not quiet:
            logger.info(f"Crawler created for platform: {config.platform.name}")
        return crawler
    
    @staticmethod
    def create_youtube_crawler(
        start_urls: List[str],
        max_depth: int = 2,
        custom_config: Optional[ApplicationConfig] = None
    ) -> Crawler:
        """
        Create a crawler configured for YouTube.
        
        Args:
            start_urls: Initial YouTube URLs to crawl
            max_depth: Maximum crawl depth
            custom_config: Custom configuration (optional)
            
        Returns:
            YouTube crawler instance
        """
        if custom_config:
            config = custom_config
        else:
            config = ApplicationConfig.for_youtube(
                crawler_config=CrawlerConfig(max_depth=max_depth)
            )
        
        return CrawlerFactory.create_crawler(config, start_urls)
    
    @staticmethod
    def create_soundcloud_crawler(
        start_urls: List[str],
        max_depth: int = 3,
        custom_config: Optional[ApplicationConfig] = None
    ) -> Crawler:
        """
        Create a crawler configured for SoundCloud.
        
        Args:
            start_urls: Initial SoundCloud URLs to crawl
            max_depth: Maximum crawl depth
            custom_config: Custom configuration (optional)
            
        Returns:
            SoundCloud crawler instance
        """
        if custom_config:
            config = custom_config
        else:
            config = ApplicationConfig.for_soundcloud(
                crawler_config=CrawlerConfig(max_depth=max_depth)
            )
        
        return CrawlerFactory.create_crawler(config, start_urls)
