"""
Core crawler implementation with proper OOP design.
"""
import logging
from typing import List, Set, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import ApplicationConfig
from .database import IDatabase
from .webdriver import IWebDriver
from .downloader import DownloadManager
from .link_extractor import ILinkExtractor
from .state_manager import StateManager
from .progress import ProgressDisplay

logger = logging.getLogger(__name__)


class Crawler:
    """
    Main crawler class implementing the crawling logic.
    Uses dependency injection for all components.
    """
    
    def __init__(
        self,
        config: ApplicationConfig,
        database: IDatabase,
        webdriver: IWebDriver,
        download_manager: DownloadManager,
        link_extractor: ILinkExtractor,
        state_manager: StateManager,
        start_urls: Optional[List[str]] = None,
        quiet: bool = False
    ):
        """
        Initialize crawler with all dependencies.
        
        Args:
            config: Application configuration
            database: Database handler
            webdriver: Web driver for page loading
            download_manager: Download manager
            link_extractor: Link extractor
            state_manager: State manager
            start_urls: Initial URLs to crawl
            quiet: If True, use minimal progress display
        """
        self.config = config
        self.database = database
        self.webdriver = webdriver
        self.download_manager = download_manager
        self.link_extractor = link_extractor
        self.state_manager = state_manager
        self.progress = ProgressDisplay(quiet=quiet)
        
        # Load or initialize state
        self.state = state_manager.load_state()
        
        # Add start URLs if provided and queue is empty
        if start_urls and not self.state.queue:
            self.state.queue = [(url, 0) for url in start_urls]
            logger.info(f"Initialized queue with {len(start_urls)} start URLs")
    
    def crawl(self) -> None:
        """Main crawling loop."""
        logger.info("Starting crawl...")
        self.progress.update(
            status="Starting crawl...",
            max_depth=self.config.crawler.max_depth
        )
        
        try:
            with ThreadPoolExecutor(max_workers=self.config.crawler.max_workers) as executor:
                while self.state.queue:
                    self._process_next_url(executor)
                    self.state_manager.save_state(self.state)
            
            self.progress.finish("Crawl completed successfully!")
        except KeyboardInterrupt:
            logger.info("Crawl interrupted by user")
            self.progress.finish("Stopped by user")
            self.state_manager.save_state(self.state)
        except Exception as e:
            logger.error(f"Crawl error: {e}")
            self.progress.error(f"Crawl error: {e}")
            self.state_manager.save_state(self.state)
            raise
        finally:
            self.close()
        
        logger.info("Crawl completed")
    
    def _process_next_url(self, executor: ThreadPoolExecutor) -> None:
        """
        Process the next URL in the queue.
        
        Args:
            executor: Thread pool executor for parallel downloads
        """
        current_url, depth = self.state.queue.pop(0)
        
        # Skip if already visited or max depth exceeded
        if current_url in self.state.visited or depth > self.config.crawler.max_depth:
            return
        
        logger.info(f'Crawling depth {depth}: {current_url}')
        self.state.visited.add(current_url)
        
        # Update progress
        self.progress.update(
            status="Crawling...",
            current_depth=depth,
            urls_processed=len(self.state.visited),
            urls_in_queue=len(self.state.queue),
            current_url=current_url
        )
        
        # Load page
        html = self.webdriver.get_page_source(
            current_url,
            self.config.crawler.scroll_count,
            self.config.crawler.scroll_pause
        )
        
        if not html:
            logger.warning(f"Failed to load page: {current_url}")
            return
        
        # Extract and download content
        content_links = self.link_extractor.extract_content_links(html)
        logger.info(f"[Depth {depth}] Found {len(content_links)} content link(s)")
        
        # Update progress with found links
        self.progress.update(
            links_found=self.progress.stats.links_found + len(content_links)
        )
        
        self._download_content(content_links, executor)
        
        # Extract and queue navigation links
        if depth < self.config.crawler.max_depth:
            nav_links = self.link_extractor.extract_navigation_links(html)
            self._queue_links(nav_links, depth + 1)
            
            # Update queue size after queuing new links
            self.progress.update(urls_in_queue=len(self.state.queue))
    
    def _download_content(self, links: Set[str], executor: ThreadPoolExecutor) -> None:
        """
        Download content from links in parallel.
        
        Args:
            links: Set of URLs to download
            executor: Thread pool executor
        """
        if not links:
            return
        
        # Submit download tasks
        futures = {
            executor.submit(
                self.download_manager.download,
                url,
                i + 1,
                len(links)
            ): url
            for i, url in enumerate(links)
        }
        
        # Process completed downloads
        for future in as_completed(futures):
            try:
                result = future.result()
                if result:
                    url, title = result
                    self.database.save_track(url, title)
                    self.database.mark_downloaded(url)
                    # Update progress - download succeeded
                    self.progress.update(
                        downloads_completed=self.progress.stats.downloads_completed + 1,
                        status="Downloading..."
                    )
            except Exception as e:
                url = futures[future]
                logger.error(f"Error downloading {url}: {e}")
                # Update progress - download failed
                self.progress.update(
                    downloads_failed=self.progress.stats.downloads_failed + 1
                )
    
    def _queue_links(self, links: Set[str], depth: int) -> None:
        """
        Add links to the crawl queue.
        
        Args:
            links: Set of URLs to queue
            depth: Depth level for these links
        """
        new_links = 0
        for link in links:
            if link not in self.state.visited and (link, depth) not in self.state.queue:
                self.state.queue.append((link, depth))
                new_links += 1
        
        if new_links > 0:
            logger.info(f"Queued {new_links} new links at depth {depth}")
    
    def close(self) -> None:
        """Clean up resources."""
        logger.info("Closing crawler resources...")
        self.webdriver.close()
        self.database.close()
        self.state_manager.save_state(self.state)
        logger.info("Crawler closed")
    
    def get_stats(self) -> dict:
        """
        Get crawler statistics.
        
        Returns:
            Dictionary with crawler stats
        """
        # Type narrowing - we know database has these methods if it's a proper implementation
        downloaded = 0
        pending = 0
        if hasattr(self.database, 'get_downloaded_count'):
            downloaded = self.database.get_downloaded_count()  # type: ignore
        if hasattr(self.database, 'get_pending_count'):
            pending = self.database.get_pending_count()  # type: ignore
            
        return {
            'queue_size': len(self.state.queue),
            'visited_count': len(self.state.visited),
            'downloaded_count': downloaded,
            'pending_count': pending
        }
