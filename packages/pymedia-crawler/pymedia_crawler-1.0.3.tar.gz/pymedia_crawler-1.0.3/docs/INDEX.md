# Documentation Index

Welcome to Media Crawler documentation! This index will help you find what you need.

## 📚 Documentation Structure

### Getting Started
- **[README](../README.md)** - Project overview, features, and quick start
- **[Quick Start Guide](QUICKSTART.md)** - Get up and running in 5 minutes
- **[Installation Guide](QUICKSTART.md#installation)** - Detailed installation instructions

### Usage Documentation
- **[Usage Guide](USAGE.md)** - Complete usage guide with examples
- **[Command Line Reference](USAGE.md#command-line-usage)** - CLI options and examples
- **[Python API Guide](USAGE.md#python-api-usage)** - Using Media Crawler as a library
- **[Common Workflows](USAGE.md#common-workflows)** - Real-world usage patterns

### API & Reference
- **[API Documentation](API.md)** - Complete API reference
- **[Configuration Reference](API.md#configuration-classes)** - All configuration options
- **[Exception Reference](API.md#exceptions)** - Error handling guide

### Architecture & Design
- **[Architecture Overview](ARCHITECTURE.md)** - System architecture and design
- **[Project Overview](PROJECT_OVERVIEW.md)** - Comprehensive project guide
- **[Design Patterns](PROJECT_OVERVIEW.md#design-patterns-used)** - Patterns implemented

### Development
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute
- **[Changelog](../CHANGELOG.md)** - Version history and changes
- **[Contributors](../CONTRIBUTORS.md)** - List of contributors

## 📖 By Topic

### Installation & Setup
1. [System Requirements](QUICKSTART.md#prerequisites)
2. [Installing Dependencies](QUICKSTART.md#installation)
3. [Verifying Installation](QUICKSTART.md#3-verify-installation)
4. [Troubleshooting Installation](USAGE.md#troubleshooting)

### Basic Usage
1. [Your First Crawl](QUICKSTART.md#your-first-crawl)
2. [CLI Examples](USAGE.md#command-line-usage)
3. [Python API Examples](USAGE.md#python-api-usage)
4. [Common Use Cases](QUICKSTART.md#common-use-cases)

### Configuration
1. [Configuration Overview](API.md#configuration-classes)
2. [Crawler Settings](API.md#crawlerconfig)
3. [Download Settings](API.md#downloadconfig)
4. [Database Settings](API.md#databaseconfig)
5. [Browser Settings](API.md#seleniumconfig)

### Advanced Topics
1. [Custom Configurations](USAGE.md#advanced-usage)
2. [Error Handling](API.md#exceptions)
3. [State Management](API.md#statemanager)
4. [Performance Tuning](USAGE.md#best-practices)
5. [Extending for New Platforms](PROJECT_OVERVIEW.md#extensibility)

### Development
1. [Setting Up Dev Environment](CONTRIBUTING.md#development-setup)
2. [Code Style Guide](CONTRIBUTING.md#coding-standards)
3. [Testing](CONTRIBUTING.md#testing)
4. [Pull Request Process](CONTRIBUTING.md#pull-request-process)

## 🎯 By User Type

### For End Users
Start here if you want to use Media Crawler:

1. **[Quick Start](QUICKSTART.md)** - Get started quickly
2. **[Usage Guide](USAGE.md)** - Learn all features
3. **[Troubleshooting](USAGE.md#troubleshooting)** - Fix common issues

### For Developers
Start here if you want to integrate Media Crawler:

1. **[API Documentation](API.md)** - API reference
2. **[Python Examples](USAGE.md#python-api-usage)** - Code examples
3. **[Architecture](ARCHITECTURE.md)** - Understand the design

### For Contributors
Start here if you want to contribute:

1. **[Contributing Guide](CONTRIBUTING.md)** - Contribution process
2. **[Project Overview](PROJECT_OVERVIEW.md)** - Project structure
3. **[Architecture](ARCHITECTURE.md)** - Technical details

## 🔍 Quick Reference

### CLI Commands
```bash
# Search and download
python cli.py youtube -k "music" -d 2

# Download from URL
python cli.py youtube -u "URL" -d 1

# Custom settings
python cli.py youtube -k "music" -d 2 -w 8 -q 320 -o ~/Music/
```

### Python API
```python
from media_crawler import CrawlerFactory, ApplicationConfig

config = ApplicationConfig.for_youtube()
crawler = CrawlerFactory.create_crawler(config=config, start_urls=["URL"])
crawler.crawl()
```

### Configuration
```python
from media_crawler import CrawlerConfig, DownloadConfig

crawler_config = CrawlerConfig(max_depth=2, max_workers=8)
download_config = DownloadConfig(audio_quality="320")
```

## 📝 Documentation Files

### Main Documentation
| File | Description |
|------|-------------|
| [README.md](../README.md) | Main project documentation |
| [QUICKSTART.md](QUICKSTART.md) | Quick start guide |
| [USAGE.md](USAGE.md) | Complete usage guide |
| [API.md](API.md) | API reference |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Architecture documentation |

### Additional Documentation
| File | Description |
|------|-------------|
| [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) | Comprehensive project guide |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines |
| [CHANGELOG.md](../CHANGELOG.md) | Version history |
| [CONTRIBUTORS.md](../CONTRIBUTORS.md) | Contributors list |
| [LICENSE](../LICENSE) | MIT License |

## 🆘 Getting Help

### Documentation Issues
- **Can't find what you need?** [Open an issue](https://github.com/HasanRagab/media-crawler/issues)
- **Found an error?** Submit a PR to fix it
- **Want to improve docs?** See [Contributing Guide](CONTRIBUTING.md)

### Using the Project
- **Installation problems?** See [Troubleshooting](USAGE.md#troubleshooting)
- **Usage questions?** Check [Usage Guide](USAGE.md)
- **API questions?** See [API Documentation](API.md)

### Development Questions
- **Architecture questions?** See [Architecture](ARCHITECTURE.md)
- **Contributing questions?** See [Contributing Guide](CONTRIBUTING.md)
- **Technical questions?** [GitHub Discussions](https://github.com/HasanRagab/media-crawler/discussions)

## 📧 Contact

- **Email**: hasanmragab@gmail.com
- **Issues**: [GitHub Issues](https://github.com/HasanRagab/media-crawler/issues)
- **Discussions**: [GitHub Discussions](https://github.com/HasanRagab/media-crawler/discussions)

## 🔗 External Resources

### Dependencies
- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [Selenium Documentation](https://www.selenium.dev/documentation/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

### Related Topics
- [Web Scraping Best Practices](https://www.scrapingbee.com/blog/web-scraping-best-practices/)
- [Python Design Patterns](https://refactoring.guru/design-patterns/python)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)

---

**Last Updated**: October 15, 2025

**Need help?** Start with the [Quick Start Guide](QUICKSTART.md) or [Usage Guide](USAGE.md)!
