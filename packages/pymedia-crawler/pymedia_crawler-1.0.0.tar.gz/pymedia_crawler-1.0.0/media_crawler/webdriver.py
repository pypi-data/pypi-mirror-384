"""
Web driver management with proper abstraction.
"""
import logging
from abc import ABC, abstractmethod
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

from .config import SeleniumConfig, CrawlerConfig
from .utils import retry
from .exceptions import NetworkException

logger = logging.getLogger(__name__)

# Try to import webdriver_manager for automatic ChromeDriver management
try:
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
    logger.info("webdriver-manager is available - will auto-download ChromeDriver if needed")
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False
    logger.debug("webdriver-manager not available - using system ChromeDriver")


class IWebDriver(ABC):
    """Interface for web driver operations."""
    
    @abstractmethod
    def get_page_source(self, url: str, scroll_count: int, scroll_pause: float) -> Optional[str]:
        """Get page source after scrolling."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close the web driver."""
        pass


class SeleniumWebDriver(IWebDriver):
    """Selenium implementation of web driver interface."""
    
    def __init__(self, selenium_config: SeleniumConfig, crawler_config: CrawlerConfig):
        """
        Initialize Selenium web driver.
        
        Args:
            selenium_config: Selenium configuration
            crawler_config: Crawler configuration for retry settings
        """
        self.selenium_config = selenium_config
        self.crawler_config = crawler_config
        self._driver: Optional[webdriver.Chrome] = None
        self._initialize_driver()
    
    def _initialize_driver(self) -> None:
        """Initialize Chrome driver with configuration."""
        try:
            logger.info("Initializing Chrome WebDriver...")
            options = self.selenium_config.get_chrome_options()
            logger.debug(f"Chrome options: headless={self.selenium_config.headless}")
            
            # Try to use webdriver-manager if available (auto-downloads ChromeDriver)
            if WEBDRIVER_MANAGER_AVAILABLE:
                try:
                    logger.info("Using webdriver-manager to handle ChromeDriver...")
                    from selenium.webdriver.chrome.service import Service  # Ensure Service is imported here
                    from webdriver_manager.chrome import ChromeDriverManager  # Ensure import is here
                    service = Service(ChromeDriverManager().install())
                    self._driver = webdriver.Chrome(service=service, options=options)
                    logger.info("Selenium WebDriver initialized successfully with webdriver-manager")
                    return
                except Exception as e:
                    logger.warning(f"webdriver-manager failed: {e}, trying system ChromeDriver...")
            
            # Fallback to system ChromeDriver
            logger.info("Using system ChromeDriver...")
            self._driver = webdriver.Chrome(options=options)
            logger.info("Selenium WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"WebDriver initialization failed: {e}")
            logger.error("\n" + "="*70)
            logger.error("CHROMEDRIVER NOT FOUND OR FAILED TO START")
            logger.error("="*70)
            logger.error("\nPlease install ChromeDriver using ONE of these methods:\n")
            logger.error("Option 1 - Arch Linux (Recommended):")
            logger.error("  sudo pacman -S chromium")
            logger.error("\nOption 2 - Automatic (webdriver-manager):")
            logger.error("  pip install webdriver-manager")
            logger.error("\nOption 3 - Manual Download:")
            logger.error("  Visit: https://chromedriver.chromium.org/downloads")
            logger.error("\nSee CHROMEDRIVER_INSTALL.md for detailed instructions")
            logger.error("="*70)
            raise NetworkException(f"Failed to initialize WebDriver: {e}")
    
    def get_page_source(self, url: str, scroll_count: int, scroll_pause: float) -> Optional[str]:
        """
        Get page source after scrolling.
        
        Args:
            url: URL to load
            scroll_count: Number of times to scroll
            scroll_pause: Pause duration between scrolls
            
        Returns:
            Page source HTML or None if failed
        """
        @retry(
            max_attempts=self.crawler_config.max_retries,
            backoff_base=self.crawler_config.retry_backoff_base,
            exceptions=(Exception,)
        )
        def _load_and_scroll():
            if not self._driver:
                raise NetworkException("WebDriver not initialized")
            
            logger.info(f"Loading page: {url}")
            self._driver.get(url)
            
            body = self._driver.find_element(By.TAG_NAME, 'body')
            for i in range(scroll_count):
                body.send_keys(Keys.END)
                time.sleep(scroll_pause)
                logger.debug(f"Scrolled {i+1}/{scroll_count}")
            
            return self._driver.page_source
        
        return _load_and_scroll()
    
    def close(self) -> None:
        """Close the web driver."""
        if self._driver:
            self._driver.quit()
            logger.info("WebDriver closed")


class WebDriverFactory:
    """Factory for creating web driver instances."""
    
    @staticmethod
    def create_driver(
        selenium_config: SeleniumConfig,
        crawler_config: CrawlerConfig,
        driver_type: str = "selenium"
    ) -> IWebDriver:
        """
        Create a web driver instance.
        
        Args:
            selenium_config: Selenium configuration
            crawler_config: Crawler configuration
            driver_type: Type of driver (currently only 'selenium' supported)
            
        Returns:
            Web driver instance
            
        Raises:
            ValueError: If driver type is not supported
        """
        if driver_type.lower() == "selenium":
            return SeleniumWebDriver(selenium_config, crawler_config)
        else:
            raise ValueError(f"Unsupported driver type: {driver_type}")
