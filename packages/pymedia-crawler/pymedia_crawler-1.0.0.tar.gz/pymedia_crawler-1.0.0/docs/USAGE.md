# Usage Guide

Complete guide to using Media Crawler for various use cases.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Command Line Usage](#command-line-usage)
- [Python API Usage](#python-api-usage)
- [Common Workflows](#common-workflows)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Installation

### System Requirements

Before installing, ensure you have:

1. **Python 3.8+**
   ```bash
   python --version
   ```

2. **Chrome/Chromium Browser**
   ```bash
   # Ubuntu/Debian
   sudo apt install chromium-browser
   
   # macOS
   brew install --cask google-chrome
   ```

3. **ChromeDriver**
   ```bash
   # Ubuntu/Debian
   sudo apt install chromium-chromedriver
   
   # macOS
   brew install chromedriver
   
   # Or use webdriver-manager (automatic)
   pip install webdriver-manager
   ```

4. **FFmpeg** (for audio conversion)
   ```bash
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # macOS
   brew install ffmpeg
   ```

### Install Media Crawler

```bash
# From source
git clone https://github.com/yourusername/media-crawler.git
cd media-crawler
pip install -r requirements.txt
pip install -e .

# Or with pip (when published)
pip install media-crawler
```

### Verify Installation

```bash
# Check if CLI works
python cli.py --help

# Run diagnostic script
python examples/diagnose.py
```

## Quick Start

### 1. Simple YouTube Download

```bash
# Search and download
python cli.py youtube -k "lofi music" -d 1
```

### 2. Download from URL

```bash
# Single URL
python cli.py youtube -u "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Multiple URLs
python cli.py youtube -u \
    "https://www.youtube.com/@channel1" \
    "https://www.youtube.com/@channel2"
```

### 3. SoundCloud

```bash
python cli.py soundcloud -u "https://soundcloud.com/artist/track" -d 2
```

## Command Line Usage

### Basic Syntax

```bash
python cli.py <platform> [input] [options]
```

### Platforms

- `youtube` - YouTube platform
- `soundcloud` - SoundCloud platform

### Input Methods

You must specify either URLs or keywords (for YouTube):

#### Using URLs (`-u, --urls`)

```bash
# Single URL
python cli.py youtube -u "https://youtube.com/watch?v=VIDEO_ID"

# Multiple URLs (space-separated)
python cli.py youtube -u \
    "https://youtube.com/@channel1" \
    "https://youtube.com/@channel2" \
    "https://youtube.com/playlist?list=PLAYLIST_ID"
```

#### Using Keywords (`-k, --keywords`)

YouTube only:

```bash
# Single keyword
python cli.py youtube -k "jazz music"

# Multiple keywords
python cli.py youtube -k "lofi" "hip hop" "beats"
```

### Configuration Options

#### Crawler Settings

**Max Depth (`-d, --depth`)**

Controls how deep the crawler goes:

```bash
# Depth 1: Only starting URLs
python cli.py youtube -u "URL" -d 1

# Depth 2: Starting URLs + linked pages
python cli.py youtube -u "URL" -d 2

# Depth 3: Starting URLs + 2 levels of links
python cli.py youtube -u "URL" -d 3
```

**Workers (`-w, --workers`)**

Number of parallel downloads:

```bash
# 4 workers (slower, less resource intensive)
python cli.py youtube -k "music" -w 4

# 16 workers (faster, more resources)
python cli.py youtube -k "music" -w 16
```

**Scroll Count (`-s, --scroll`)**

Number of page scrolls (for lazy-loaded content):

```bash
# Scroll 5 times (faster, fewer items)
python cli.py youtube -k "music" -s 5

# Scroll 20 times (slower, more items)
python cli.py youtube -k "music" -s 20
```

#### Download Settings

**Output Directory (`-o, --output`)**

Where to save downloads:

```bash
# Custom directory
python cli.py youtube -k "music" -o ~/Music/YouTube/

# Current directory
python cli.py youtube -k "music" -o ./downloads/
```

**Audio Quality (`-q, --quality`)**

Bitrate in kbps:

```bash
# Standard quality (192 kbps)
python cli.py youtube -k "music" -q 192

# High quality (320 kbps)
python cli.py youtube -k "music" -q 320

# Low quality (128 kbps)
python cli.py youtube -k "music" -q 128
```

#### Other Options

**Verbose Mode (`-v, --verbose`)**

Enable detailed logging:

```bash
python cli.py youtube -k "music" -v
```

**Browser Mode (`--headless/--no-headless`)**

```bash
# Headless (default, no GUI)
python cli.py youtube -k "music" --headless

# Show browser window
python cli.py youtube -k "music" --no-headless
```

**State Management (`--resume/--no-resume`)**

```bash
# Resume from last state (default)
python cli.py youtube -k "music" --resume

# Start fresh
python cli.py youtube -k "music" --no-resume
```

### Complete Examples

#### YouTube Examples

```bash
# Basic search with default settings
python cli.py youtube -k "ambient music"

# Advanced search with custom settings
python cli.py youtube -k "classical piano" \
    -d 3 \
    -w 12 \
    -s 15 \
    -o ~/Music/Classical/ \
    -q 320 \
    -v

# Crawl multiple channels
python cli.py youtube -u \
    "https://youtube.com/@LofiGirl" \
    "https://youtube.com/@ChilledCow" \
    -d 2 \
    -w 8

# Download from playlist
python cli.py youtube -u \
    "https://youtube.com/playlist?list=PLxxxxxxxxxxxxxxx" \
    -d 1

# Multiple search terms
python cli.py youtube -k \
    "jazz" \
    "blues" \
    "soul" \
    -d 2 \
    -o ~/Music/Jazz/
```

#### SoundCloud Examples

```bash
# Basic crawl
python cli.py soundcloud -u "https://soundcloud.com/discover"

# Artist/user page
python cli.py soundcloud -u \
    "https://soundcloud.com/artist-name" \
    -d 2

# Multiple starting points
python cli.py soundcloud -u \
    "https://soundcloud.com/artist1" \
    "https://soundcloud.com/artist2" \
    -d 1 \
    -w 16
```

## Python API Usage

### Basic Usage

```python
from media_crawler import CrawlerFactory, ApplicationConfig

# Create configuration
config = ApplicationConfig.for_youtube()

# Create crawler
crawler = CrawlerFactory.create_crawler(
    config=config,
    start_urls=["https://www.youtube.com/watch?v=example"]
)

# Run crawler
try:
    crawler.crawl()
except KeyboardInterrupt:
    print("Stopped by user")
finally:
    crawler.close()
```

### Custom Configuration

```python
from media_crawler import (
    ApplicationConfig,
    CrawlerConfig,
    DownloadConfig,
    CrawlerFactory
)

# Detailed configuration
crawler_config = CrawlerConfig(
    max_depth=3,
    max_workers=16,
    scroll_count=20,
    max_retries=5
)

download_config = DownloadConfig(
    download_folder="~/Music/Custom/",
    audio_quality="320",
    audio_format="mp3"
)

# Create application config
config = ApplicationConfig.for_youtube(
    crawler_config=crawler_config,
    download_config=download_config
)

# Create and run crawler
crawler = CrawlerFactory.create_crawler(
    config=config,
    start_urls=["https://youtube.com/example"]
)

crawler.crawl()
```

### Multiple Platforms

```python
from media_crawler import CrawlerFactory

# YouTube crawler
youtube_crawler = CrawlerFactory.create_youtube_crawler(
    start_urls=["https://youtube.com/example"],
    max_depth=2
)

# SoundCloud crawler
soundcloud_crawler = CrawlerFactory.create_soundcloud_crawler(
    start_urls=["https://soundcloud.com/example"],
    max_depth=2
)

# Run both
youtube_crawler.crawl()
soundcloud_crawler.crawl()
```

## Common Workflows

### Workflow 1: Build a Music Library

```bash
# Step 1: Search for genres
python cli.py youtube -k "jazz" -d 2 -o ~/Music/Jazz/
python cli.py youtube -k "classical" -d 2 -o ~/Music/Classical/
python cli.py youtube -k "electronic" -d 2 -o ~/Music/Electronic/

# Step 2: Follow specific channels
python cli.py youtube -u \
    "https://youtube.com/@jazz-channel" \
    "https://youtube.com/@classical-channel" \
    -d 1

# Step 3: High-quality downloads
python cli.py youtube -k "audiophile recordings" \
    -q 320 \
    -o ~/Music/HQ/
```

### Workflow 2: Download Playlists

```bash
# Single playlist
python cli.py youtube -u \
    "https://youtube.com/playlist?list=PLxxxxxxxx" \
    -d 1 \
    -o ~/Music/Playlists/MyPlaylist/

# Multiple playlists
python cli.py youtube -u \
    "https://youtube.com/playlist?list=PLxxxxxxxx" \
    "https://youtube.com/playlist?list=PLyyyyyyyy" \
    -d 1
```

### Workflow 3: Archive Channel Content

```bash
# Deep crawl of channel
python cli.py youtube -u \
    "https://youtube.com/@channel-name" \
    -d 3 \
    -w 16 \
    -s 20 \
    -o ~/Archives/ChannelName/

# Resume if interrupted
python cli.py youtube -u \
    "https://youtube.com/@channel-name" \
    -d 3 \
    --resume
```

### Workflow 4: Discover New Music

```bash
# Start with discovery page
python cli.py soundcloud -u \
    "https://soundcloud.com/discover" \
    -d 2 \
    -w 12

# Or YouTube trending
python cli.py youtube -u \
    "https://youtube.com/feed/trending?bp=4gIcGhpnYW1pbmdfY29ycHVzX21vc3RfcG9wdWxhcg%3D%3D" \
    -d 2
```

## Advanced Usage

### Using Python API with Context Manager

```python
from media_crawler import CrawlerFactory, ApplicationConfig

config = ApplicationConfig.for_youtube()
crawler = CrawlerFactory.create_crawler(config=config, start_urls=["URL"])

try:
    crawler.crawl()
finally:
    crawler.close()  # Always close resources
```

### Custom Platform Configuration

```python
from media_crawler import (
    ApplicationConfig,
    PlatformConfig,
    CrawlerFactory
)

# Define custom platform
custom_platform = PlatformConfig(
    name="MyPlatform",
    base_domain="myplatform.com",
    base_url="https://myplatform.com",
    ignore_words=["login", "signup", "privacy"]
)

# Create config
config = ApplicationConfig(
    platform_config=custom_platform,
    # ... other configs
)

# Note: You'll need custom link extractor for new platforms
```

### Monitoring Progress

```python
from media_crawler import CrawlerFactory, ApplicationConfig

config = ApplicationConfig.for_youtube()
crawler = CrawlerFactory.create_crawler(
    config=config,
    start_urls=["URL"],
    quiet=False  # Show progress
)

# Access progress statistics
crawler.crawl()

# Check database for stats
from media_crawler import DatabaseFactory

db = DatabaseFactory.create_database(config.database)
print(f"Downloaded: {db.get_downloaded_count()}")
print(f"Pending: {db.get_pending_count()}")
db.close()
```

### Batch Processing

```python
from media_crawler import CrawlerFactory, ApplicationConfig

# List of URLs to process
urls_batch = [
    ["https://youtube.com/channel1", "https://youtube.com/channel2"],
    ["https://youtube.com/channel3", "https://youtube.com/channel4"],
    ["https://youtube.com/channel5", "https://youtube.com/channel6"],
]

for batch in urls_batch:
    config = ApplicationConfig.for_youtube()
    crawler = CrawlerFactory.create_crawler(
        config=config,
        start_urls=batch
    )
    
    try:
        crawler.crawl()
    except Exception as e:
        print(f"Error processing batch: {e}")
        continue
    finally:
        crawler.close()
```

## Troubleshooting

### Common Issues

#### 1. ChromeDriver Not Found

**Problem**: `selenium.common.exceptions.WebDriverException: 'chromedriver' executable needs to be in PATH`

**Solution**:
```bash
# Option 1: Install system-wide
sudo apt install chromium-chromedriver  # Linux
brew install chromedriver  # macOS

# Option 2: Use webdriver-manager
pip install webdriver-manager
# Code will auto-download chromedriver
```

#### 2. FFmpeg Not Found

**Problem**: Audio conversion fails

**Solution**:
```bash
# Install FFmpeg
sudo apt install ffmpeg  # Linux
brew install ffmpeg  # macOS
```

#### 3. Permission Denied

**Problem**: Cannot write to output directory

**Solution**:
```bash
# Check permissions
ls -la ~/Music/

# Create directory with proper permissions
mkdir -p ~/Music/Downloads/
chmod 755 ~/Music/Downloads/
```

#### 4. SSL Certificate Errors

**Problem**: `ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]`

**Solution**: Already handled by default config with `nocheckcertificate=True`

#### 5. Memory Issues

**Problem**: Out of memory errors

**Solution**:
```bash
# Reduce workers
python cli.py youtube -k "music" -w 4

# Reduce scroll count
python cli.py youtube -k "music" -s 5

# Process in batches
```

#### 6. Rate Limiting

**Problem**: Too many requests, getting blocked

**Solution**:
```bash
# Reduce workers
python cli.py youtube -k "music" -w 2

# Add delays (modify config)
```

### Debug Mode

Enable verbose logging:

```bash
# CLI
python cli.py youtube -k "music" -v

# Python API
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check System

Run diagnostic script:

```bash
python examples/diagnose.py
```

## Best Practices

### 1. Start Small

Begin with small depths and fewer workers:

```bash
# Start with depth 1
python cli.py youtube -k "music" -d 1 -w 4

# Gradually increase
python cli.py youtube -k "music" -d 2 -w 8
```

### 2. Use Appropriate Quality

Match quality to use case:

```bash
# For testing: 128 kbps
python cli.py youtube -k "music" -q 128

# For normal use: 192 kbps (default)
python cli.py youtube -k "music" -q 192

# For archiving: 320 kbps
python cli.py youtube -k "music" -q 320
```

### 3. Organize Output

Use descriptive directories:

```bash
python cli.py youtube -k "jazz" -o ~/Music/Jazz/
python cli.py youtube -k "classical" -o ~/Music/Classical/
python cli.py youtube -k "ambient" -o ~/Music/Ambient/
```

### 4. Monitor Resources

```bash
# Check disk space
df -h ~/Music/

# Monitor during crawl
htop  # or top
```

### 5. Resume Long Crawls

For large crawls, use resume:

```bash
# Start crawl
python cli.py youtube -k "music" -d 3 --resume

# If interrupted, simply run again
python cli.py youtube -k "music" -d 3 --resume
```

### 6. Respect Platforms

- Don't use too many workers
- Don't crawl too deeply
- Follow platform terms of service
- Use reasonable delays

### 7. Clean Up

Periodically clean database:

```bash
# Check size
du -h youtube.db

# Backup before cleaning
cp youtube.db youtube.db.backup
```

## Tips & Tricks

### Tip 1: Quick Test

Test before large crawl:

```bash
# Test with depth 1, few workers
python cli.py youtube -u "URL" -d 1 -w 2 --no-headless
```

### Tip 2: Parallel Instances

Run multiple instances for different platforms:

```bash
# Terminal 1
python cli.py youtube -k "music" -d 2 &

# Terminal 2
python cli.py soundcloud -u "URL" -d 2 &
```

### Tip 3: Scheduling

Use cron for regular downloads:

```bash
# Add to crontab
0 2 * * * cd /path/to/media-crawler && python cli.py youtube -k "daily music" -d 1
```

### Tip 4: Filtering

Use specific keywords:

```bash
# Instead of broad "music"
python cli.py youtube -k "music"

# Be specific
python cli.py youtube -k "mozart piano concerto"
```

### Tip 5: Database Queries

Query database directly:

```bash
sqlite3 youtube.db "SELECT COUNT(*) FROM tracks WHERE downloaded=1;"
sqlite3 youtube.db "SELECT title FROM tracks LIMIT 10;"
```

---

For more information, see:
- [README.md](../README.md) - Overview and quick start
- [API.md](API.md) - Detailed API documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture details
