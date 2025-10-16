"""
Configuration module for the crawler application.
Centralizes all configuration settings for easy management and extension.
"""
import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CrawlerConfig:
    """Configuration for web crawler behavior."""
    max_depth: int = 2
    max_workers: int = 8
    scroll_count: int = 10
    scroll_pause: float = 0.5
    max_retries: int = 3
    retry_backoff_base: int = 2
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.max_depth < 0:
            raise ValueError("max_depth must be non-negative")
        if self.max_workers < 1:
            raise ValueError("max_workers must be at least 1")
        if self.max_retries < 1:
            raise ValueError("max_retries must be at least 1")


@dataclass
class DatabaseConfig:
    """Configuration for database settings."""
    db_path: str = "crawler.db"
    check_same_thread: bool = False
    
    def __post_init__(self):
        """Ensure database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)


@dataclass
class DownloadConfig:
    """Configuration for download settings."""
    download_folder: str = field(default_factory=lambda: os.path.expanduser('~/Music/Downloads/'))
    format: str = 'bestaudio/best'
    audio_format: str = 'mp3'
    audio_quality: str = '192'
    quiet: bool = True
    no_warnings: bool = True
    nocheckcertificate: bool = True
    user_agent: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    
    def __post_init__(self):
        """Ensure download folder exists."""
        os.makedirs(self.download_folder, exist_ok=True)


@dataclass
class SeleniumConfig:
    """Configuration for Selenium WebDriver."""
    headless: bool = True
    disable_gpu: bool = True
    no_sandbox: bool = True
    disable_dev_shm_usage: bool = True
    log_level: int = 3
    
    def get_chrome_options(self):
        """Generate Chrome options from configuration."""
        from selenium.webdriver.chrome.options import Options
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        if self.disable_gpu:
            options.add_argument('--disable-gpu')
        if self.no_sandbox:
            options.add_argument('--no-sandbox')
        if self.disable_dev_shm_usage:
            options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'--log-level={self.log_level}')
        return options


@dataclass
class PlatformConfig:
    """Platform-specific configuration (YouTube, SoundCloud, etc.)."""
    name: str
    base_domain: str
    base_url: str
    ignore_words: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Set default ignore words if not provided."""
        if not self.ignore_words:
            self.ignore_words = [
                'pages', 'cookies', 'page', 'charts', 'followers', 
                'you', 'your', 'library', 'directory', 'people', 'tag', 'tags'
            ]


class ApplicationConfig:
    """Main application configuration aggregating all sub-configs."""
    
    def __init__(
        self,
        platform_config: PlatformConfig,
        crawler_config: Optional[CrawlerConfig] = None,
        database_config: Optional[DatabaseConfig] = None,
        download_config: Optional[DownloadConfig] = None,
        selenium_config: Optional[SeleniumConfig] = None
    ):
        self.platform = platform_config
        self.crawler = crawler_config or CrawlerConfig()
        self.database = database_config or DatabaseConfig(
            db_path=f"{platform_config.name.lower()}.db"
        )
        self.download = download_config or DownloadConfig(
            download_folder=os.path.expanduser(f'~/Music/{platform_config.name}/')
        )
        self.selenium = selenium_config or SeleniumConfig()
    
    @classmethod
    def for_youtube(cls, **kwargs):
        """Create configuration for YouTube platform."""
        platform = PlatformConfig(
            name="YouTube",
            base_domain="youtube.com",
            base_url="https://www.youtube.com"
        )
        return cls(platform, **kwargs)
    
    @classmethod
    def for_soundcloud(cls, **kwargs):
        """Create configuration for SoundCloud platform."""
        platform = PlatformConfig(
            name="SoundCloud",
            base_domain="soundcloud.com",
            base_url="https://soundcloud.com"
        )
        return cls(platform, **kwargs)
