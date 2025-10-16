"""
Comprehensive examples demonstrating various use cases of the media crawler.
"""
import logging

from media_crawler.config import (
    ApplicationConfig, CrawlerConfig, DatabaseConfig,
    DownloadConfig, SeleniumConfig, PlatformConfig
)
from media_crawler.factory import CrawlerFactory
from media_crawler.exceptions import CrawlerException

logging.basicConfig(
    format='%(asctime)s | %(levelname)s | %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# =============================================================================
# BASIC EXAMPLES
# =============================================================================

def example_01_simple_youtube():
    """Example 1: Simplest possible YouTube crawler."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Simple YouTube Crawler")
    print("="*70)
    
    start_urls = ['https://youtube.com/results?search_query=lofi']
    crawler = CrawlerFactory.create_youtube_crawler(start_urls, max_depth=1)
    
    try:
        crawler.crawl()
        print(f"\nStats: {crawler.get_stats()}")
    finally:
        crawler.close()


def example_02_simple_soundcloud():
    """Example 2: Simplest possible SoundCloud crawler."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Simple SoundCloud Crawler")
    print("="*70)
    
    start_urls = ['https://soundcloud.com/discover']
    crawler = CrawlerFactory.create_soundcloud_crawler(start_urls, max_depth=2)
    
    try:
        crawler.crawl()
        print(f"\nStats: {crawler.get_stats()}")
    finally:
        crawler.close()


def example_03_multiple_keywords():
    """Example 3: Crawl multiple search keywords."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Multiple Keywords")
    print("="*70)
    
    keywords = ['ambient music', 'jazz', 'classical piano']
    start_urls = [
        f'https://youtube.com/results?search_query={kw}' 
        for kw in keywords
    ]
    
    crawler = CrawlerFactory.create_youtube_crawler(start_urls, max_depth=1)
    
    try:
        crawler.crawl()
        print(f"\nStats: {crawler.get_stats()}")
    finally:
        crawler.close()


# =============================================================================
# CUSTOMIZATION EXAMPLES
# =============================================================================

def example_04_custom_download_settings():
    """Example 4: Custom download quality and format."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Custom Download Settings")
    print("="*70)
    
    # High quality MP3 downloads
    download_config = DownloadConfig(
        download_folder='~/Music/HighQuality/',
        audio_quality='320',  # 320 kbps
        audio_format='mp3'
    )
    
    config = ApplicationConfig.for_youtube(
        download_config=download_config,
        crawler_config=CrawlerConfig(max_depth=1)
    )
    
    start_urls = ['https://youtube.com/results?search_query=classical']
    crawler = CrawlerFactory.create_crawler(config, start_urls)
    
    try:
        crawler.crawl()
        print(f"\nStats: {crawler.get_stats()}")
    finally:
        crawler.close()


def example_05_high_performance():
    """Example 5: High-performance configuration with more workers."""
    print("\n" + "="*70)
    print("EXAMPLE 5: High Performance Configuration")
    print("="*70)
    
    crawler_config = CrawlerConfig(
        max_depth=3,
        max_workers=20,  # More parallel downloads
        scroll_count=20,  # Scroll more to find more content
        scroll_pause=0.2,  # Faster scrolling
        max_retries=5
    )
    
    config = ApplicationConfig.for_youtube(
        crawler_config=crawler_config
    )
    
    start_urls = ['https://youtube.com/results?search_query=edm']
    crawler = CrawlerFactory.create_crawler(config, start_urls)
    
    try:
        crawler.crawl()
        print(f"\nStats: {crawler.get_stats()}")
    finally:
        crawler.close()


def example_06_custom_database():
    """Example 6: Custom database location and organization."""
    print("\n" + "="*70)
    print("EXAMPLE 6: Custom Database")
    print("="*70)
    
    database_config = DatabaseConfig(
        db_path='data/music_collection.db'
    )
    
    download_config = DownloadConfig(
        download_folder='~/Music/MyCollection/'
    )
    
    config = ApplicationConfig.for_youtube(
        database_config=database_config,
        download_config=download_config,
        crawler_config=CrawlerConfig(max_depth=2)
    )
    
    start_urls = ['https://youtube.com/results?search_query=indie']
    crawler = CrawlerFactory.create_crawler(config, start_urls)
    
    try:
        crawler.crawl()
        print(f"\nStats: {crawler.get_stats()}")
    finally:
        crawler.close()


def example_07_visible_browser():
    """Example 7: Run with visible browser (not headless) for debugging."""
    print("\n" + "="*70)
    print("EXAMPLE 7: Visible Browser Mode")
    print("="*70)
    
    selenium_config = SeleniumConfig(
        headless=False  # Show the browser
    )
    
    config = ApplicationConfig.for_youtube(
        selenium_config=selenium_config,
        crawler_config=CrawlerConfig(max_depth=1, scroll_count=5)
    )
    
    start_urls = ['https://youtube.com/results?search_query=test']
    crawler = CrawlerFactory.create_crawler(config, start_urls)
    
    try:
        crawler.crawl()
        print(f"\nStats: {crawler.get_stats()}")
    finally:
        crawler.close()


def example_08_custom_platform():
    """Example 8: Create a completely custom platform configuration."""
    print("\n" + "="*70)
    print("EXAMPLE 8: Custom Platform Configuration")
    print("="*70)
    
    # Custom YouTube configuration with specific ignore list
    platform_config = PlatformConfig(
        name="YouTube",
        base_domain="youtube.com",
        base_url="https://www.youtube.com",
        ignore_words=[
            'ads', 'premium', 'live', 'shorts',  # Filter out these
            'trending', 'subscriptions'
        ]
    )
    
    crawler_config = CrawlerConfig(
        max_depth=2,
        max_workers=10,
        scroll_count=15
    )
    
    config = ApplicationConfig(
        platform_config=platform_config,
        crawler_config=crawler_config
    )
    
    start_urls = ['https://youtube.com/results?search_query=tutorial']
    crawler = CrawlerFactory.create_crawler(config, start_urls)
    
    try:
        crawler.crawl()
        print(f"\nStats: {crawler.get_stats()}")
    finally:
        crawler.close()


# =============================================================================
# ADVANCED EXAMPLES
# =============================================================================

def example_09_resume_interrupted_crawl():
    """Example 9: Resume an interrupted crawl using state management."""
    print("\n" + "="*70)
    print("EXAMPLE 9: Resume Interrupted Crawl")
    print("="*70)
    
    start_urls = ['https://youtube.com/results?search_query=podcast']
    
    # First run - simulate interruption
    print("Starting initial crawl (will be 'interrupted')...")
    crawler = CrawlerFactory.create_youtube_crawler(start_urls, max_depth=2)
    
    try:
        # In real scenario, this might be interrupted
        crawler.crawl()
    finally:
        crawler.close()
    
    # Second run - resumes from state
    print("\nResuming crawl from saved state...")
    crawler2 = CrawlerFactory.create_youtube_crawler(start_urls, max_depth=2)
    
    try:
        crawler2.crawl()
        print(f"\nFinal Stats: {crawler2.get_stats()}")
    finally:
        crawler2.close()


def example_10_sequential_crawls():
    """Example 10: Run multiple crawls sequentially with different configs."""
    print("\n" + "="*70)
    print("EXAMPLE 10: Sequential Multi-Crawl")
    print("="*70)
    
    configs = [
        ('lofi', 1, '~/Music/Lofi/'),
        ('jazz', 1, '~/Music/Jazz/'),
        ('classical', 1, '~/Music/Classical/')
    ]
    
    for keyword, depth, folder in configs:
        print(f"\n--- Crawling: {keyword} ---")
        
        download_config = DownloadConfig(download_folder=folder)
        config = ApplicationConfig.for_youtube(
            download_config=download_config,
            crawler_config=CrawlerConfig(max_depth=depth)
        )
        
        start_urls = [f'https://youtube.com/results?search_query={keyword}']
        crawler = CrawlerFactory.create_crawler(config, start_urls)
        
        try:
            crawler.crawl()
            print(f"Stats for {keyword}: {crawler.get_stats()}")
        finally:
            crawler.close()


def example_11_error_handling():
    """Example 11: Proper error handling."""
    print("\n" + "="*70)
    print("EXAMPLE 11: Error Handling")
    print("="*70)
    
    start_urls = ['https://youtube.com/results?search_query=test']
    crawler = CrawlerFactory.create_youtube_crawler(start_urls, max_depth=1)
    
    try:
        crawler.crawl()
        stats = crawler.get_stats()
        print(f"\nSuccess! Stats: {stats}")
        
    except CrawlerException as e:
        logger.error(f"Crawler-specific error: {e}")
        # Handle crawler errors
        
    except KeyboardInterrupt:
        logger.info("Crawl interrupted by user")
        # Save state is automatic
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        # Handle other errors
        
    finally:
        # Always clean up
        crawler.close()
        print("\nCrawler closed properly")


def example_12_monitoring_progress():
    """Example 12: Monitor crawl progress."""
    print("\n" + "="*70)
    print("EXAMPLE 12: Progress Monitoring")
    print("="*70)
    
    start_urls = ['https://youtube.com/results?search_query=music']
    crawler = CrawlerFactory.create_youtube_crawler(start_urls, max_depth=2)
    
    try:
        # Check initial state
        print(f"Initial state: {crawler.get_stats()}")
        
        # Start crawl
        crawler.crawl()
        
        # Check final state
        final_stats = crawler.get_stats()
        print(f"\nFinal Statistics:")
        print(f"  - Queue size: {final_stats['queue_size']}")
        print(f"  - Visited URLs: {final_stats['visited_count']}")
        print(f"  - Downloaded: {final_stats['downloaded_count']}")
        print(f"  - Pending: {final_stats['pending_count']}")
        
    finally:
        crawler.close()


# =============================================================================
# MAIN RUNNER
# =============================================================================

def run_all_examples():
    """Run all examples (commented out by default)."""
    examples = [
        # example_01_simple_youtube,
        # example_02_simple_soundcloud,
        # example_03_multiple_keywords,
        # example_04_custom_download_settings,
        # example_05_high_performance,
        # example_06_custom_database,
        # example_07_visible_browser,
        # example_08_custom_platform,
        # example_09_resume_interrupted_crawl,
        # example_10_sequential_crawls,
        example_11_error_handling,
        # example_12_monitoring_progress,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            logger.error(f"Example {example.__name__} failed: {e}")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("MEDIA CRAWLER - COMPREHENSIVE EXAMPLES")
    print("="*70)
    print("\nUncomment examples in run_all_examples() to execute them.")
    print("Each example demonstrates a different feature or use case.")
    print("="*70 + "\n")
    
    run_all_examples()
