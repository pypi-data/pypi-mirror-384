# API Documentation

Complete API reference for the Media Crawler package.

## Table of Contents

- [Configuration Classes](#configuration-classes)
- [Main Classes](#main-classes)
- [Interfaces](#interfaces)
- [Exceptions](#exceptions)
- [Utilities](#utilities)

## Configuration Classes

### `ApplicationConfig`

Main application configuration aggregating all sub-configurations.

```python
from media_crawler import ApplicationConfig

config = ApplicationConfig(
    platform_config=platform_config,
    crawler_config=crawler_config,
    database_config=database_config,
    download_config=download_config,
    selenium_config=selenium_config
)
```

#### Factory Methods

##### `for_youtube(**kwargs)`

Create configuration for YouTube platform.

```python
config = ApplicationConfig.for_youtube(
    crawler_config=CrawlerConfig(max_depth=3),
    download_config=DownloadConfig(audio_quality="320")
)
```

**Parameters:**
- `crawler_config` (CrawlerConfig, optional): Crawler configuration
- `database_config` (DatabaseConfig, optional): Database configuration
- `download_config` (DownloadConfig, optional): Download configuration
- `selenium_config` (SeleniumConfig, optional): Selenium configuration

**Returns:** `ApplicationConfig` instance configured for YouTube

##### `for_soundcloud(**kwargs)`

Create configuration for SoundCloud platform.

```python
config = ApplicationConfig.for_soundcloud(
    crawler_config=CrawlerConfig(max_depth=2)
)
```

**Parameters:** Same as `for_youtube()`

**Returns:** `ApplicationConfig` instance configured for SoundCloud

---

### `CrawlerConfig`

Configuration for web crawler behavior.

```python
from media_crawler import CrawlerConfig

config = CrawlerConfig(
    max_depth=2,
    max_workers=8,
    scroll_count=10,
    scroll_pause=0.5,
    max_retries=3,
    retry_backoff_base=2
)
```

#### Attributes

- **max_depth** (int, default=2): Maximum crawl depth
- **max_workers** (int, default=8): Number of parallel download workers
- **scroll_count** (int, default=10): Number of page scrolls for dynamic content
- **scroll_pause** (float, default=0.5): Pause between scrolls in seconds
- **max_retries** (int, default=3): Maximum retry attempts for failed operations
- **retry_backoff_base** (int, default=2): Base for exponential backoff calculation

#### Validation

Raises `ValueError` if:
- `max_depth` is negative
- `max_workers` is less than 1
- `max_retries` is less than 1

---

### `DatabaseConfig`

Configuration for database settings.

```python
from media_crawler import DatabaseConfig

config = DatabaseConfig(
    db_path="data/youtube.db",
    check_same_thread=False
)
```

#### Attributes

- **db_path** (str, default="crawler.db"): Path to SQLite database file
- **check_same_thread** (bool, default=False): SQLite thread safety check

#### Notes

- Automatically creates database directory if it doesn't exist
- Directory is created in `__post_init__()` method

---

### `DownloadConfig`

Configuration for download settings.

```python
from media_crawler import DownloadConfig

config = DownloadConfig(
    download_folder="~/Music/Downloads/",
    format="bestaudio/best",
    audio_format="mp3",
    audio_quality="320",
    quiet=True
)
```

#### Attributes

- **download_folder** (str, default="~/Music/Downloads/"): Output directory for downloads
- **format** (str, default="bestaudio/best"): yt-dlp format specification
- **audio_format** (str, default="mp3"): Target audio codec
- **audio_quality** (str, default="192"): Audio bitrate in kbps
- **quiet** (bool, default=True): Suppress yt-dlp output
- **no_warnings** (bool, default=True): Suppress yt-dlp warnings
- **nocheckcertificate** (bool, default=True): Disable SSL certificate verification
- **user_agent** (str): HTTP User-Agent string

#### Notes

- Automatically creates download folder if it doesn't exist
- Supports tilde (~) expansion for home directory

---

### `SeleniumConfig`

Configuration for Selenium WebDriver.

```python
from media_crawler import SeleniumConfig

config = SeleniumConfig(
    headless=True,
    disable_gpu=True,
    no_sandbox=True,
    disable_dev_shm_usage=True,
    log_level=3
)
```

#### Attributes

- **headless** (bool, default=True): Run browser in headless mode
- **disable_gpu** (bool, default=True): Disable GPU hardware acceleration
- **no_sandbox** (bool, default=True): Disable Chrome sandbox
- **disable_dev_shm_usage** (bool, default=True): Disable /dev/shm usage
- **log_level** (int, default=3): Chrome logging level (0=ALL, 3=SEVERE)

#### Methods

##### `get_chrome_options()`

Generate Chrome options from configuration.

```python
options = config.get_chrome_options()
```

**Returns:** `selenium.webdriver.chrome.options.Options` object

---

### `PlatformConfig`

Platform-specific configuration.

```python
from media_crawler import PlatformConfig

config = PlatformConfig(
    name="YouTube",
    base_domain="youtube.com",
    base_url="https://www.youtube.com",
    ignore_words=["cookies", "privacy", "terms"]
)
```

#### Attributes

- **name** (str): Platform name
- **base_domain** (str): Domain for URL validation
- **base_url** (str): Base URL for resolving relative links
- **ignore_words** (List[str]): Words to filter from URLs

#### Default Ignore Words

If not provided, defaults to:
```python
['pages', 'cookies', 'page', 'charts', 'followers', 
 'you', 'your', 'library', 'directory', 'people', 'tag', 'tags']
```

---

## Main Classes

### `Crawler`

Main crawler class implementing the crawling logic.

```python
from media_crawler import Crawler

crawler = Crawler(
    config=config,
    database=database,
    webdriver=webdriver,
    download_manager=download_manager,
    link_extractor=link_extractor,
    state_manager=state_manager,
    start_urls=["https://example.com"],
    quiet=False
)
```

#### Constructor Parameters

- **config** (ApplicationConfig): Application configuration
- **database** (IDatabase): Database handler
- **webdriver** (IWebDriver): Web driver instance
- **download_manager** (DownloadManager): Download manager
- **link_extractor** (ILinkExtractor): Link extractor
- **state_manager** (StateManager): State manager
- **start_urls** (List[str], optional): Initial URLs to crawl
- **quiet** (bool, default=False): Minimal progress display

#### Methods

##### `crawl()`

Start the crawling process.

```python
crawler.crawl()
```

**Returns:** None

**Raises:**
- `CrawlerException`: On crawler errors
- `KeyboardInterrupt`: When user interrupts

**Behavior:**
- Processes URLs from queue until empty
- Automatically saves state periodically
- Handles interruption gracefully
- Closes resources on completion

##### `close()`

Close all resources (database, webdriver, etc.).

```python
crawler.close()
```

**Returns:** None

---

### `CrawlerFactory`

Factory for creating fully configured crawler instances.

```python
from media_crawler import CrawlerFactory

crawler = CrawlerFactory.create_crawler(
    config=config,
    start_urls=start_urls,
    quiet=False
)
```

#### Static Methods

##### `create_crawler(config, start_urls=None, state_file_name=None, quiet=False)`

Create a fully configured crawler instance.

```python
crawler = CrawlerFactory.create_crawler(
    config=ApplicationConfig.for_youtube(),
    start_urls=["https://www.youtube.com/watch?v=example"],
    quiet=False
)
```

**Parameters:**
- **config** (ApplicationConfig): Application configuration
- **start_urls** (List[str], optional): Initial URLs to crawl
- **state_file_name** (str, optional): Deprecated, kept for compatibility
- **quiet** (bool, default=False): Minimal progress display

**Returns:** Configured `Crawler` instance

##### `create_youtube_crawler(start_urls, max_depth=2, custom_config=None)`

Create a crawler configured for YouTube.

```python
crawler = CrawlerFactory.create_youtube_crawler(
    start_urls=["https://www.youtube.com/watch?v=example"],
    max_depth=3
)
```

**Parameters:**
- **start_urls** (List[str]): Initial YouTube URLs
- **max_depth** (int, default=2): Maximum crawl depth
- **custom_config** (ApplicationConfig, optional): Custom configuration

**Returns:** YouTube `Crawler` instance

##### `create_soundcloud_crawler(start_urls, max_depth=2, custom_config=None)`

Create a crawler configured for SoundCloud.

```python
crawler = CrawlerFactory.create_soundcloud_crawler(
    start_urls=["https://soundcloud.com/artist/track"],
    max_depth=2
)
```

**Parameters:**
- **start_urls** (List[str]): Initial SoundCloud URLs
- **max_depth** (int, default=2): Maximum crawl depth
- **custom_config** (ApplicationConfig, optional): Custom configuration

**Returns:** SoundCloud `Crawler` instance

---

### `DownloadManager`

Manager for parallel download execution.

```python
from media_crawler import DownloadManager

manager = DownloadManager(strategy, max_workers=8)
```

#### Constructor Parameters

- **strategy** (IDownloadStrategy): Download strategy implementation
- **max_workers** (int): Maximum parallel workers

#### Methods

##### `download_tracks(tracks)`

Download multiple tracks in parallel.

```python
results = manager.download_tracks([
    ("https://example.com/track1", 1, 10),
    ("https://example.com/track2", 2, 10),
])
```

**Parameters:**
- **tracks** (List[Tuple[str, int, int]]): List of (url, index, total)

**Returns:** List of (url, title) tuples for successful downloads

---

### `StateManager`

Manager for crawler state persistence.

```python
from media_crawler import StateManager

manager = StateManager()
```

#### Methods

##### `load_state()`

Load crawler state.

```python
state = manager.load_state()
```

**Returns:** `CrawlerState` object with:
- `queue`: List of (url, depth) tuples
- `visited`: Set of visited URLs

##### `save_state(state)`

Save crawler state.

```python
manager.save_state(state)
```

**Parameters:**
- **state** (CrawlerState): State to save

**Returns:** None

##### `clear_state()`

Clear saved state.

```python
manager.clear_state()
```

**Returns:** None

---

## Interfaces

### `IDatabase`

Interface for database operations.

#### Methods

##### `save_track(url, title)`

Save a track to the database.

```python
database.save_track(
    url="https://example.com/track",
    title="Track Title"
)
```

##### `is_downloaded(url)`

Check if a track has been downloaded.

```python
if database.is_downloaded("https://example.com/track"):
    print("Already downloaded")
```

##### `mark_downloaded(url)`

Mark a track as downloaded.

```python
database.mark_downloaded("https://example.com/track")
```

##### `get_all_tracks()`

Get all tracks from the database.

```python
tracks = database.get_all_tracks()
# Returns: List[Tuple[url, title, downloaded, downloaded_at]]
```

##### `get_downloaded_count()`

Get count of downloaded tracks.

```python
count = database.get_downloaded_count()
```

##### `get_pending_count()`

Get count of pending tracks.

```python
count = database.get_pending_count()
```

##### `close()`

Close the database connection.

```python
database.close()
```

---

### `IWebDriver`

Interface for web driver operations.

#### Methods

##### `get_page_source(url, scroll_count, scroll_pause)`

Load page and return HTML source.

```python
html = webdriver.get_page_source(
    url="https://example.com",
    scroll_count=10,
    scroll_pause=0.5
)
```

##### `quit()`

Close the web driver.

```python
webdriver.quit()
```

---

### `ILinkExtractor`

Interface for link extraction strategies.

#### Methods

##### `extract_content_links(html)`

Extract links to downloadable content.

```python
links = extractor.extract_content_links(html)
# Returns: Set[str]
```

##### `extract_navigation_links(html)`

Extract links for further crawling.

```python
links = extractor.extract_navigation_links(html)
# Returns: Set[str]
```

---

### `IDownloadStrategy`

Interface for download strategies.

#### Methods

##### `download(url, index, total)`

Download a track/video.

```python
result = strategy.download(
    url="https://example.com/track",
    index=1,
    total=10
)
# Returns: Optional[Tuple[str, str]] - (url, title) or None
```

---

## Exceptions

All exceptions inherit from `CrawlerException`.

### `CrawlerException`

Base exception for all crawler-related errors.

```python
from media_crawler import CrawlerException

try:
    # crawler operations
    pass
except CrawlerException as e:
    print(f"Crawler error: {e}")
```

### `DatabaseException`

Exception for database-related errors.

```python
from media_crawler import DatabaseException

try:
    database.save_track(url, title)
except DatabaseException as e:
    print(f"Database error: {e}")
```

### `DownloadException`

Exception for download-related errors.

```python
from media_crawler import DownloadException

try:
    manager.download_tracks(tracks)
except DownloadException as e:
    print(f"Download error: {e}")
```

### `NetworkException`

Exception for network-related errors.

```python
from media_crawler import NetworkException

try:
    html = webdriver.get_page_source(url)
except NetworkException as e:
    print(f"Network error: {e}")
```

### `ConfigurationException`

Exception for configuration-related errors.

```python
from media_crawler import ConfigurationException

try:
    config = CrawlerConfig(max_depth=-1)
except ConfigurationException as e:
    print(f"Configuration error: {e}")
```

---

## Utilities

### `retry` Decorator

Decorator for retrying functions with exponential backoff.

```python
from media_crawler.utils import retry

@retry(max_attempts=3, backoff_base=2, exceptions=(Exception,))
def unstable_function():
    # May fail
    pass
```

**Parameters:**
- **max_attempts** (int): Maximum retry attempts
- **backoff_base** (int): Base for exponential backoff
- **exceptions** (Tuple[Exception]): Exceptions to catch

### `url_to_filename`

Convert URL to safe filename.

```python
from media_crawler.utils import url_to_filename

filename = url_to_filename("https://example.com/path?query=1")
# Returns: "example.com_path_query_1"
```

**Parameters:**
- **url** (str): URL to convert

**Returns:** Safe filename string

---

## Complete Example

```python
from media_crawler import (
    ApplicationConfig,
    CrawlerConfig,
    DownloadConfig,
    CrawlerFactory,
    CrawlerException
)

# Configure
config = ApplicationConfig.for_youtube(
    crawler_config=CrawlerConfig(
        max_depth=2,
        max_workers=8
    ),
    download_config=DownloadConfig(
        download_folder="~/Music/YouTube/",
        audio_quality="320"
    )
)

# Create crawler
crawler = CrawlerFactory.create_crawler(
    config=config,
    start_urls=[
        "https://www.youtube.com/watch?v=example1",
        "https://www.youtube.com/watch?v=example2"
    ]
)

# Run
try:
    crawler.crawl()
except KeyboardInterrupt:
    print("Interrupted by user")
except CrawlerException as e:
    print(f"Error: {e}")
finally:
    crawler.close()
```
