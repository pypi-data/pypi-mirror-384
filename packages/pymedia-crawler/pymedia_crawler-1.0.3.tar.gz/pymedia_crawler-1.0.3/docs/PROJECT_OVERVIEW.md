# Project Overview

## Media Crawler - A Comprehensive Guide

### What is Media Crawler?

Media Crawler is a robust, extensible Python application for downloading media content from various platforms. It uses web scraping, browser automation, and parallel processing to efficiently crawl and download content.

### Key Features

#### 🎯 Core Functionality
- **Multi-platform Support**: YouTube, SoundCloud, easily extensible
- **Smart Crawling**: Depth-based traversal with intelligent link filtering
- **Parallel Processing**: Multi-threaded downloads for performance
- **State Management**: Resume interrupted crawls seamlessly
- **Database Tracking**: Prevent duplicates, track download history

#### 🛠️ Technical Excellence
- **SOLID Principles**: Clean architecture, maintainable code
- **Design Patterns**: Factory, Strategy, Dependency Injection
- **Type Safety**: Full type hints throughout
- **Comprehensive Testing**: Unit tests for core components
- **Excellent Documentation**: README, API docs, guides, examples

#### 🎨 User Experience
- **Beautiful CLI**: Rich progress indicators and status updates
- **Flexible API**: Use as library or standalone application
- **Configurable**: Extensive configuration options
- **Error Handling**: Robust error handling with automatic retries

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Application Layer                       │
│  ┌──────────────┐              ┌──────────────┐            │
│  │     CLI      │              │  Python API  │            │
│  └──────┬───────┘              └──────┬───────┘            │
└─────────┼──────────────────────────────┼──────────────────┘
          │                              │
          └──────────────┬───────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│                    Service Layer                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              CrawlerFactory                             │ │
│  │  (Creates and configures all components)               │ │
│  └────────────────────────┬───────────────────────────────┘ │
└───────────────────────────┼───────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐
│   Crawler    │    │   Config    │    │   Database  │
│  (Orchestr.) │    │  (Settings) │    │  (Tracking) │
└───────┬──────┘    └─────────────┘    └─────────────┘
        │
        ├──────────┬──────────┬──────────┬──────────┐
        │          │          │          │          │
   ┌────▼────┐┌───▼────┐┌────▼────┐┌───▼────┐┌────▼────┐
   │WebDriver││Download││  Link   ││ State  ││Progress │
   │(Browser)││Manager ││Extractor││Manager ││Display  │
   └─────────┘└────────┘└─────────┘└────────┘└─────────┘
```

### Component Breakdown

#### 1. Configuration Layer
- **ApplicationConfig**: Main configuration aggregator
- **CrawlerConfig**: Crawler behavior settings
- **DatabaseConfig**: Database connection settings
- **DownloadConfig**: Download options and quality
- **SeleniumConfig**: Browser automation settings
- **PlatformConfig**: Platform-specific settings

#### 2. Core Components

**Crawler**
- Main orchestration logic
- Manages crawl queue and visited URLs
- Coordinates other components
- Handles interruptions gracefully

**Database (IDatabase)**
- SQLite-based storage
- Track downloaded content
- Prevent duplicates
- Thread-safe operations

**WebDriver (IWebDriver)**
- Selenium-based browser automation
- Handle dynamic content (JavaScript)
- Scroll pages for lazy-loaded content
- Capture full page HTML

**DownloadManager**
- Parallel download execution
- Thread pool management
- Retry logic with exponential backoff
- Progress tracking

**LinkExtractor (ILinkExtractor)**
- Platform-specific link extraction
- Content link identification
- Navigation link discovery
- URL filtering and validation

**StateManager**
- In-memory state management
- Queue persistence
- Visited URL tracking

**ProgressDisplay**
- Real-time progress updates
- Statistics display
- Clean single-page output
- Terminal detection

#### 3. Utility Layer
- **retry decorator**: Automatic retry with backoff
- **url_to_filename**: Safe filename conversion
- **exponential_backoff_sleep**: Smart retry delays

#### 4. Exception Hierarchy
```
CrawlerException (base)
├── DatabaseException
├── DownloadException
├── NetworkException
├── ConfigurationException
└── ValidationException
```

### Design Patterns Used

#### 1. Factory Pattern
**CrawlerFactory** creates fully configured instances:
```python
crawler = CrawlerFactory.create_crawler(config, start_urls)
```

Benefits:
- Encapsulates complex initialization
- Consistent object creation
- Easy to extend with new platforms

#### 2. Strategy Pattern
**IDownloadStrategy** and **ILinkExtractor**:
```python
# Different strategies for different platforms
youtube_extractor = YouTubeLinkExtractor(...)
soundcloud_extractor = SoundCloudLinkExtractor(...)
```

Benefits:
- Easy to add new platforms
- Swap implementations at runtime
- Clean separation of concerns

#### 3. Dependency Injection
Components receive dependencies:
```python
def __init__(self, database: IDatabase, webdriver: IWebDriver, ...):
    self.database = database
    self.webdriver = webdriver
```

Benefits:
- Testability (easy to mock)
- Loose coupling
- Flexible configuration

#### 4. Interface Segregation
Multiple focused interfaces:
- **IDatabase**: Database operations
- **IWebDriver**: Browser operations
- **ILinkExtractor**: Link extraction
- **IDownloadStrategy**: Download operations

Benefits:
- Clear contracts
- Easy to implement alternatives
- Forces good design

### Data Flow

#### Crawling Flow
```
1. Start URLs added to queue
2. Pop URL from queue
3. Load page with WebDriver
4. Extract links with LinkExtractor
   ├─→ Content links → DownloadManager
   └─→ Navigation links → Add to queue
5. Mark URL as visited
6. Save state
7. Repeat from step 2
```

#### Download Flow
```
1. Content links identified
2. Check database for duplicates
3. Submit to DownloadManager
4. Parallel download execution
   ├─→ Extract info (yt-dlp)
   ├─→ Download media
   ├─→ Convert audio (FFmpeg)
   └─→ Save to folder
5. Mark as downloaded in database
6. Update progress display
```

### Key Technologies

#### Core Libraries
- **Python 3.8+**: Modern Python features
- **Selenium**: Browser automation
- **yt-dlp**: Media downloading
- **BeautifulSoup**: HTML parsing
- **SQLite**: Database storage

#### Development Tools
- **pytest**: Testing framework
- **black**: Code formatting
- **flake8**: Linting
- **mypy**: Type checking

### Project Structure

```
media-crawler/
├── media_crawler/          # Main package
│   ├── __init__.py        # Public API exports
│   ├── config.py          # Configuration classes
│   ├── crawler.py         # Main crawler logic
│   ├── factory.py         # Factory for component creation
│   ├── database.py        # Database interface & implementation
│   ├── webdriver.py       # Browser automation
│   ├── downloader.py      # Download management
│   ├── link_extractor.py  # Link extraction strategies
│   ├── state_manager.py   # State persistence
│   ├── progress.py        # Progress display
│   ├── utils.py           # Utility functions
│   └── exceptions.py      # Custom exceptions
│
├── tests/                 # Unit tests
├── examples/              # Example scripts
├── docs/                  # Documentation
│   ├── ARCHITECTURE.md    # Architecture details
│   ├── API.md            # API documentation
│   ├── USAGE.md          # Usage guide
│   ├── QUICKSTART.md     # Quick start guide
│   └── CONTRIBUTING.md   # Contribution guidelines
│
├── cli.py                # Command-line interface
├── setup.py              # Package setup
├── requirements.txt      # Dependencies
├── README.md             # Main documentation
├── CHANGELOG.md          # Version history
├── CONTRIBUTORS.md       # Contributors list
└── LICENSE               # MIT License
```

### Development Principles

#### 1. SOLID Principles
- **S**ingle Responsibility: Each class has one job
- **O**pen/Closed: Open for extension, closed for modification
- **L**iskov Substitution: Interfaces are properly implemented
- **I**nterface Segregation: Focused, minimal interfaces
- **D**ependency Inversion: Depend on abstractions, not concretions

#### 2. Code Quality
- Type hints throughout
- Comprehensive docstrings
- Unit tests for core logic
- Linting with flake8
- Formatting with black

#### 3. Documentation
- Clear README with examples
- Detailed API documentation
- Architecture documentation
- Usage guides
- Code comments where needed

### Performance Considerations

#### 1. Parallel Processing
- Thread pool for downloads
- Configurable worker count
- Non-blocking operations

#### 2. Caching & Deduplication
- Database tracks downloads
- Visited URL set prevents re-crawling
- File existence checks

#### 3. Resource Management
- Proper cleanup in finally blocks
- Context managers where applicable
- Connection pooling

### Security Considerations

#### 1. Input Validation
- URL validation
- Configuration validation
- Safe filename conversion

#### 2. Network Security
- HTTPS by default
- Configurable SSL verification
- Rate limiting considerations

#### 3. File System
- Safe path handling
- Directory creation with proper permissions
- No arbitrary file operations

### Extensibility

#### Adding New Platforms

1. **Create PlatformConfig**:
```python
spotify_config = PlatformConfig(
    name="Spotify",
    base_domain="spotify.com",
    base_url="https://open.spotify.com"
)
```

2. **Implement ILinkExtractor**:
```python
class SpotifyLinkExtractor(BaseLinkExtractor):
    def extract_content_links(self, html: str) -> Set[str]:
        # Implementation
        pass
    
    def extract_navigation_links(self, html: str) -> Set[str]:
        # Implementation
        pass
```

3. **Register in Factory**:
```python
@staticmethod
def create_spotify_crawler(start_urls, max_depth=2):
    config = ApplicationConfig.for_spotify()
    return CrawlerFactory.create_crawler(config, start_urls)
```

### Testing Strategy

#### 1. Unit Tests
- Test individual components
- Mock external dependencies
- Cover edge cases

#### 2. Integration Tests
- Test component interactions
- Use test fixtures
- Verify data flow

#### 3. Manual Testing
- End-to-end workflows
- Different platforms
- Various configurations

### Future Enhancements

#### Planned Features
- Additional platforms (Spotify, Apple Music)
- GUI interface
- REST API
- Docker containerization
- Cloud storage integration
- Advanced filtering
- Plugin system

#### Technical Improvements
- Async/await for better performance
- Distributed crawling
- Better error recovery
- Enhanced progress tracking
- Monitoring and metrics

### Contributing

We welcome contributions! See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for:
- Development setup
- Coding standards
- Pull request process
- Issue guidelines

### License

MIT License - see [LICENSE](LICENSE) file.

### Contact

- **Author**: Hasan Ragab
- **Email**: hasanmragbn@gmail.com
- **Issues**: [GitHub Issues](https://github.com/HasanRagab/media-crawler/issues)
- **Discussions**: [GitHub Discussions](https://github.com/HasanRagab/media-crawler/discussions)

---

**Last Updated**: October 15, 2025
**Version**: 1.0.3
