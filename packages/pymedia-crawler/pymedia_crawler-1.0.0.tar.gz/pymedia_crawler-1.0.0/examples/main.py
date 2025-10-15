"""
Main application entry point with examples.
Demonstrates how to use the refactored crawler with full user control.
"""
import logging
from typing import List

from media_crawler.config import (
    ApplicationConfig, CrawlerConfig, DatabaseConfig, 
    DownloadConfig, SeleniumConfig, PlatformConfig
)
from media_crawler.factory import CrawlerFactory
from media_crawler.exceptions import CrawlerException

# Configure logging
logging.basicConfig(
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def crawl_youtube_simple(keywords: List[str], max_depth: int = 2) -> None:
    """
    Simple YouTube crawler using factory defaults.
    
    Args:
        keywords: Search keywords for YouTube
        max_depth: Maximum crawl depth
    """
    logger.info("Starting simple YouTube crawler")
    
    # Generate search URLs
    start_urls = [f'https://youtube.com/results?search_query={kw}' for kw in keywords]
    
    # Create crawler using factory
    crawler = CrawlerFactory.create_youtube_crawler(start_urls, max_depth)
    
    try:
        crawler.crawl()
        stats = crawler.get_stats()
        logger.info(f"Crawl completed. Stats: {stats}")
    except CrawlerException as e:
        logger.error(f"Crawler error: {e}")
    finally:
        crawler.close()


def crawl_soundcloud_simple(start_urls: List[str], max_depth: int = 3) -> None:
    """
    Simple SoundCloud crawler using factory defaults.
    
    Args:
        start_urls: Starting URLs for SoundCloud
        max_depth: Maximum crawl depth
    """
    logger.info("Starting simple SoundCloud crawler")
    
    # Create crawler using factory
    crawler = CrawlerFactory.create_soundcloud_crawler(start_urls, max_depth)
    
    try:
        crawler.crawl()
        stats = crawler.get_stats()
        logger.info(f"Crawl completed. Stats: {stats}")
    except CrawlerException as e:
        logger.error(f"Crawler error: {e}")
    finally:
        crawler.close()


def crawl_youtube_custom(keywords: List[str]) -> None:
    """
    Advanced YouTube crawler with custom configuration.
    Demonstrates full user control over all settings.
    
    Args:
        keywords: Search keywords for YouTube
    """
    logger.info("Starting custom YouTube crawler")
    
    # Create custom configurations
    crawler_config = CrawlerConfig(
        max_depth=3,
        max_workers=16,  # More parallel downloads
        scroll_count=15,  # Scroll more to find more content
        scroll_pause=0.3,
        max_retries=5,
        retry_backoff_base=2
    )
    
    database_config = DatabaseConfig(
        db_path='data/youtube_custom.db'
    )
    
    download_config = DownloadConfig(
        download_folder='~/Music/YouTube_Custom/',
        audio_quality='320',  # Higher quality
        audio_format='mp3'
    )
    
    selenium_config = SeleniumConfig(
        headless=True,
        disable_gpu=True
    )
    
    platform_config = PlatformConfig(
        name="YouTube",
        base_domain="youtube.com",
        base_url="https://www.youtube.com",
        ignore_words=['ads', 'premium', 'live']  # Custom ignore list
    )
    
    # Create application config
    config = ApplicationConfig(
        platform_config=platform_config,
        crawler_config=crawler_config,
        database_config=database_config,
        download_config=download_config,
        selenium_config=selenium_config
    )
    
    # Generate start URLs
    start_urls = [f'https://youtube.com/results?search_query={kw}' for kw in keywords]
    
    # Create crawler with custom config
    crawler = CrawlerFactory.create_crawler(config, start_urls)
    
    try:
        crawler.crawl()
        stats = crawler.get_stats()
        logger.info(f"Custom crawl completed. Stats: {stats}")
    except CrawlerException as e:
        logger.error(f"Crawler error: {e}")
    finally:
        crawler.close()


def crawl_multiple_platforms() -> None:
    """
    Example of crawling multiple platforms sequentially.
    """
    logger.info("Starting multi-platform crawler")
    
    # Crawl YouTube
    youtube_keywords = ['lofi hip hop', 'jazz music']
    crawl_youtube_simple(youtube_keywords, max_depth=2)
    
    # Crawl SoundCloud
    soundcloud_urls = [
        'https://soundcloud.com/discover',
        'https://soundcloud.com/charts'
    ]
    crawl_soundcloud_simple(soundcloud_urls, max_depth=2)


def main():
    """Main entry point with examples."""
    
    # Example 1: Simple YouTube crawl
    logger.info("=== Example 1: Simple YouTube Crawl ===")
    crawl_youtube_simple(keywords=['ambient music'], max_depth=1)
    
    # Example 2: Simple SoundCloud crawl
    # logger.info("=== Example 2: Simple SoundCloud Crawl ===")
    # crawl_soundcloud_simple(
    #     start_urls=['https://soundcloud.com/discover'],
    #     max_depth=2
    # )
    
    # Example 3: Custom configuration
    # logger.info("=== Example 3: Custom YouTube Crawl ===")
    # crawl_youtube_custom(keywords=['classical music'])
    
    # Example 4: Multiple platforms
    # logger.info("=== Example 4: Multi-Platform Crawl ===")
    # crawl_multiple_platforms()


if __name__ == '__main__':
    main()
