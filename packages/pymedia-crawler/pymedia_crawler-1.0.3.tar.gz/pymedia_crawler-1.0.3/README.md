# Media Crawler

A robust, extensible web crawler for downloading media content from YouTube, SoundCloud, and other platforms. Built with modern Python design patterns and best practices.

## 📋 Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
  - [Command Line Interface](#command-line-interface)
  - [Python API](#python-api)
- [Configuration](#configuration)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Development](#development)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

- 🎵 **Multi-Platform Support**: YouTube, SoundCloud, and easily extensible to other platforms
- 🔄 **Smart Crawling**: Depth-based crawling with configurable parameters
- ⚡ **Parallel Downloads**: Multi-threaded download manager for fast processing
- 💾 **State Management**: Resume interrupted crawls seamlessly
- 🗄️ **Database Tracking**: SQLite-based tracking to avoid duplicate downloads
- 🎨 **Beautiful CLI**: Rich progress indicators and status updates
- 🏗️ **SOLID Design**: Clean architecture with dependency injection
- 🛡️ **Robust Error Handling**: Automatic retries with exponential backoff
- ⚙️ **Highly Configurable**: Extensive configuration options for all components

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- Chrome/Chromium browser
- ChromeDriver (or use webdriver-manager for automatic installation)
- FFmpeg (for audio conversion)

### Install from source

```bash
# Clone the repository
git clone https://github.com/HasanRagab/media-crawler.git
cd media-crawler

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Install with pip (when published)

```bash
pip install media-crawler
```

## 🚀 Quick Start

### Using the Command Line

```bash
# Download from YouTube search
python cli.py youtube -k "lofi hip hop" "jazz music" -d 2

# Download from specific YouTube URLs
python cli.py youtube -u "https://youtube.com/@channel" -d 1

# Download from SoundCloud
python cli.py soundcloud -u "https://soundcloud.com/discover" -d 3
```

### Using the Python API

```python
from media_crawler import CrawlerFactory, ApplicationConfig

# Create configuration
config = ApplicationConfig.for_youtube()

# Create crawler
crawler = CrawlerFactory.create_crawler(
    config=config,
    start_urls=["https://www.youtube.com/watch?v=example"]
)

# Start crawling
crawler.crawl()
```

## 📖 Usage

### Command Line Interface

The CLI provides a simple interface to the crawler functionality:

```bash
python cli.py <platform> [options]
```

#### Arguments

- `platform`: Platform to crawl (`youtube` or `soundcloud`)

#### Options

**Input Options** (mutually exclusive):
- `-u, --urls URL [URL ...]`: Starting URLs to crawl
- `-k, --keywords KEYWORD [KEYWORD ...]`: Search keywords (YouTube only)

**Crawler Settings**:
- `-d, --depth N`: Maximum crawl depth (default: 2)
- `-w, --workers N`: Number of parallel download workers (default: 8)
- `-s, --scroll N`: Number of page scrolls (default: 10)

**Download Settings**:
- `-o, --output DIR`: Output folder for downloads
- `-q, --quality QUALITY`: Audio quality/bitrate (default: 192)

**Other Options**:
- `-v, --verbose`: Enable verbose logging
- `--headless/--no-headless`: Run browser in headless mode (default: True)
- `--resume`: Resume from previous state (default: True)
- `--no-resume`: Start fresh, clearing previous state

#### Examples

```bash
# Basic YouTube search with keywords
python cli.py youtube -k "ambient music" -d 2

# Multiple search terms
python cli.py youtube -k "lofi" "jazz" "chill" -d 3

# Crawl specific YouTube channels
python cli.py youtube -u "https://youtube.com/@channel1" "https://youtube.com/@channel2"

# SoundCloud with custom output directory
python cli.py soundcloud -u "https://soundcloud.com/discover" -o ~/Music/SoundCloud/

# High quality downloads with more workers
python cli.py youtube -k "classical music" -q 320 -w 16

# Verbose mode for debugging
python cli.py youtube -k "music" -d 1 -v

# Non-headless mode to see browser
python cli.py youtube -u "https://youtube.com/example" --no-headless

# Start fresh without resuming
python cli.py youtube -k "music" --no-resume
```

### Python API

For more control, use the Python API directly:

#### Basic Usage

```python
from media_crawler import (
    ApplicationConfig,
    CrawlerFactory,
    CrawlerConfig,
    DownloadConfig
)

# Create configuration
config = ApplicationConfig.for_youtube(
    crawler_config=CrawlerConfig(
        max_depth=2,
        max_workers=8,
        scroll_count=10
    ),
    download_config=DownloadConfig(
        download_folder="~/Music/YouTube/",
        audio_quality="320"
    )
)

# Create and run crawler
crawler = CrawlerFactory.create_crawler(
    config=config,
    start_urls=["https://www.youtube.com/watch?v=example"]
)

crawler.crawl()
```

#### Advanced Configuration

```python
from media_crawler import (
    ApplicationConfig,
    CrawlerConfig,
    DatabaseConfig,
    DownloadConfig,
    SeleniumConfig,
    PlatformConfig
)

# Custom platform configuration
platform = PlatformConfig(
    name="CustomPlatform",
    base_domain="example.com",
    base_url="https://example.com",
    ignore_words=["login", "signup", "privacy"]
)

# Detailed configurations
crawler_config = CrawlerConfig(
    max_depth=3,
    max_workers=16,
    scroll_count=20,
    scroll_pause=0.5,
    max_retries=5,
    retry_backoff_base=2
)

database_config = DatabaseConfig(
    db_path="data/custom.db",
    check_same_thread=False
)

download_config = DownloadConfig(
    download_folder="~/Downloads/Media/",
    format="bestaudio/best",
    audio_format="mp3",
    audio_quality="320",
    quiet=False
)

selenium_config = SeleniumConfig(
    headless=True,
    disable_gpu=True,
    no_sandbox=True
)

# Create application config
config = ApplicationConfig(
    platform_config=platform,
    crawler_config=crawler_config,
    database_config=database_config,
    download_config=download_config,
    selenium_config=selenium_config
)

# Create and run crawler
from media_crawler import CrawlerFactory

crawler = CrawlerFactory.create_crawler(
    config=config,
    start_urls=["https://example.com/start"]
)

crawler.crawl()
```

#### Error Handling

```python
from media_crawler import (
    CrawlerFactory,
    ApplicationConfig,
    CrawlerException,
    DatabaseException,
    DownloadException
)

try:
    config = ApplicationConfig.for_youtube()
    crawler = CrawlerFactory.create_crawler(
        config=config,
        start_urls=["https://www.youtube.com/watch?v=example"]
    )
    crawler.crawl()
except DatabaseException as e:
    print(f"Database error: {e}")
except DownloadException as e:
    print(f"Download error: {e}")
except CrawlerException as e:
    print(f"Crawler error: {e}")
except KeyboardInterrupt:
    print("Crawl interrupted by user")
```

## ⚙️ Configuration

### Configuration Classes

The crawler uses a hierarchical configuration system:

#### `CrawlerConfig`
Controls crawler behavior:
- `max_depth`: Maximum crawl depth (default: 2)
- `max_workers`: Number of parallel workers (default: 8)
- `scroll_count`: Number of page scrolls (default: 10)
- `scroll_pause`: Pause between scrolls in seconds (default: 0.5)
- `max_retries`: Maximum retry attempts (default: 3)
- `retry_backoff_base`: Exponential backoff base (default: 2)

#### `DatabaseConfig`
Database settings:
- `db_path`: Path to SQLite database (default: "crawler.db")
- `check_same_thread`: SQLite thread safety (default: False)

#### `DownloadConfig`
Download settings:
- `download_folder`: Output directory (default: "~/Music/Downloads/")
- `format`: Video/audio format (default: "bestaudio/best")
- `audio_format`: Audio codec (default: "mp3")
- `audio_quality`: Bitrate (default: "192")
- `quiet`: Suppress yt-dlp output (default: True)
- `user_agent`: HTTP user agent string

#### `SeleniumConfig`
Browser automation settings:
- `headless`: Run browser in headless mode (default: True)
- `disable_gpu`: Disable GPU acceleration (default: True)
- `no_sandbox`: Disable Chrome sandbox (default: True)
- `disable_dev_shm_usage`: Disable /dev/shm usage (default: True)
- `log_level`: Chrome log level (default: 3)

#### `PlatformConfig`
Platform-specific settings:
- `name`: Platform name
- `base_domain`: Domain for URL validation
- `base_url`: Base URL for relative links
- `ignore_words`: Words to filter out from URLs

### Environment Variables

You can override default settings using environment variables:

```bash
export MEDIA_CRAWLER_DOWNLOAD_FOLDER="~/Music/Downloads/"
export MEDIA_CRAWLER_MAX_DEPTH=3
export MEDIA_CRAWLER_MAX_WORKERS=16
export MEDIA_CRAWLER_HEADLESS=true
```

## 🏗️ Architecture

The project follows SOLID principles and uses several design patterns:

### Design Patterns

1. **Factory Pattern**: `CrawlerFactory` creates fully configured crawler instances
2. **Strategy Pattern**: Different download and link extraction strategies
3. **Dependency Injection**: Components are injected rather than created internally
4. **Interface Segregation**: Abstract base classes define clear contracts

### Core Components

```
┌─────────────────┐
│   CrawlerFactory │  ← Entry point, creates all components
└────────┬────────┘
         │
         ├──→ ┌──────────┐
         │    │ Crawler  │  ← Main orchestrator
         │    └────┬─────┘
         │         │
         │         ├──→ Database (IDatabase)
         │         ├──→ WebDriver (IWebDriver)
         │         ├──→ DownloadManager
         │         ├──→ LinkExtractor (ILinkExtractor)
         │         ├──→ StateManager
         │         └──→ ProgressDisplay
         │
         └──→ ApplicationConfig
              ├── CrawlerConfig
              ├── DatabaseConfig
              ├── DownloadConfig
              ├── SeleniumConfig
              └── PlatformConfig
```

### Component Details

- **Crawler**: Main orchestration logic, manages crawl loop
- **Database**: Tracks downloaded content, prevents duplicates
- **WebDriver**: Handles page loading and JavaScript rendering
- **DownloadManager**: Parallel download execution with retry logic
- **LinkExtractor**: Platform-specific link extraction strategies
- **StateManager**: Saves/loads crawler state for resumption
- **ProgressDisplay**: Real-time progress updates

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

## 📁 Project Structure

```
media-crawler/
├── cli.py                      # Command-line interface
├── setup.py                    # Package setup
├── pyproject.toml             # Project metadata
├── requirements.txt           # Dependencies
├── Makefile                   # Build and test automation
├── LICENSE                    # MIT License
│
├── media_crawler/             # Main package
│   ├── __init__.py           # Package exports
│   ├── config.py             # Configuration classes
│   ├── crawler.py            # Main crawler logic
│   ├── factory.py            # Factory for creating crawlers
│   ├── database.py           # Database interface & implementation
│   ├── webdriver.py          # Selenium WebDriver wrapper
│   ├── downloader.py         # Download manager & strategies
│   ├── link_extractor.py     # Link extraction strategies
│   ├── state_manager.py      # State persistence
│   ├── progress.py           # Progress display
│   ├── utils.py              # Utility functions
│   └── exceptions.py         # Custom exceptions
│
├── tests/                     # Unit tests
│   ├── test_config.py
│   ├── test_crawler.py
│   ├── test_database.py
│   └── ...
│
├── examples/                  # Example scripts
│   ├── main.py               # Basic usage example
│   ├── examples.py           # Various usage examples
│   └── diagnose.py           # Diagnostic script
│
├── docs/                      # Documentation
│   ├── ARCHITECTURE.md       # Architecture details
│   └── API.md                # API documentation
│
└── scripts/                   # Utility scripts
    ├── QUICKSTART.py
    ├── PROJECT_OVERVIEW.py
    └── ORGANIZATION_SUMMARY.py
```

## 🔧 Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/HasanRagab/media-crawler.git
cd media-crawler

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -r requirements.txt
pip install -e ".[dev]"
```

### Code Style

The project uses:
- **black** for code formatting
- **flake8** for linting
- **mypy** for type checking

```bash
# Format code
make format

# Run linters
make lint

# Type checking
make typecheck
```

### Project Commands (Makefile)

```bash
make help          # Show available commands
make install       # Install package and dependencies
make dev-install   # Install with development dependencies
make format        # Format code with black
make lint          # Run flake8 linter
make typecheck     # Run mypy type checker
make test          # Run tests
make test-coverage # Run tests with coverage report
make clean         # Clean build artifacts
make build         # Build distribution packages
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=media_crawler --cov-report=html

# Run specific test file
pytest tests/test_crawler.py

# Run with verbose output
pytest -v
```

### Write Tests

Tests are organized by module:

```python
# tests/test_crawler.py
import pytest
from media_crawler import Crawler, ApplicationConfig

def test_crawler_initialization():
    config = ApplicationConfig.for_youtube()
    # ... test code
```

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature`
3. **Make your changes**
4. **Write tests** for new functionality
5. **Ensure tests pass**: `pytest`
6. **Format code**: `make format`
7. **Commit changes**: `git commit -am 'Add new feature'`
8. **Push to branch**: `git push origin feature/your-feature`
9. **Submit pull request**

### Code Guidelines

- Follow PEP 8 style guide
- Write docstrings for all public methods
- Add type hints
- Keep functions focused and small
- Write unit tests for new features
- Update documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Excellent YouTube downloader
- [Selenium](https://www.selenium.dev/) - Browser automation
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - HTML parsing
- [Rich](https://github.com/Textualize/rich) - Beautiful terminal formatting

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/HasanRagab/media-crawler/issues)
- **Discussions**: [GitHub Discussions](https://github.com/HasanRagab/media-crawler/discussions)
- **Email**: hasanmragab@gmail.com

## 🗺️ Roadmap

- [ ] Add support for more platforms (Spotify, Apple Music)
- [ ] Implement GUI interface
- [ ] Add playlist management
- [ ] Support for video downloads
- [ ] Docker containerization
- [ ] Cloud storage integration
- [ ] REST API interface
- [ ] Real-time monitoring dashboard

---

**Made with ❤️ by Hasan Ragab**
