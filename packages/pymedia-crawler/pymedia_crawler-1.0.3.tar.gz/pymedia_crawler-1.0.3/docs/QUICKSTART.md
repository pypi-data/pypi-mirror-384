# Quick Start Guide

Get started with Media Crawler in under 5 minutes!

## Prerequisites

Before you begin, ensure you have:

- ✅ Python 3.8 or higher
- ✅ Chrome or Chromium browser
- ✅ FFmpeg (for audio conversion)

## Installation

### 1. Install System Dependencies

<details>
<summary><b>Ubuntu/Debian</b></summary>

```bash
sudo apt update
sudo apt install chromium-browser chromium-chromedriver ffmpeg
```
</details>

<details>
<summary><b>Arch Linux</b></summary>

```bash
sudo pacman -S chromium ffmpeg
```
</details>

<details>
<summary><b>macOS</b></summary>

```bash
brew install chromium chromedriver ffmpeg
```
</details>

### 2. Install Media Crawler

```bash
# Clone the repository
git clone https://github.com/HasanRagab/media-crawler.git
cd media-crawler

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install package
pip install -e .
```

### 3. Verify Installation

```bash
python cli.py --help
```

You should see the help menu. If you do, you're ready to go! 🎉

## Your First Crawl

### Example 1: Search YouTube

```bash
python cli.py youtube -k "lofi music" -d 1
```

This will:
- 🔍 Search YouTube for "lofi music"
- 📥 Download tracks (up to depth 1)
- 💾 Save to `~/Music/YouTube/`

### Example 2: Download from URL

```bash
python cli.py youtube -u "https://www.youtube.com/watch?v=jfKfPfyJRdk"
```

This will:
- 🎵 Download the specific video
- 🎧 Convert to MP3
- 💾 Save to `~/Music/YouTube/`

### Example 3: SoundCloud

```bash
python cli.py soundcloud -u "https://soundcloud.com/discover" -d 2
```

This will:
- 🔍 Crawl SoundCloud discover page
- 📥 Download tracks (up to depth 2)
- 💾 Save to `~/Music/SoundCloud/`

## Common Options

### Control Download Quality

```bash
# High quality (320 kbps)
python cli.py youtube -k "music" -q 320

# Standard quality (192 kbps - default)
python cli.py youtube -k "music" -q 192

# Low quality (128 kbps)
python cli.py youtube -k "music" -q 128
```

### Control Crawl Depth

```bash
# Depth 1: Only starting URLs
python cli.py youtube -u "URL" -d 1

# Depth 2: Starting URLs + linked pages
python cli.py youtube -u "URL" -d 2

# Depth 3: Starting URLs + 2 levels of links
python cli.py youtube -u "URL" -d 3
```

### Change Output Directory

```bash
python cli.py youtube -k "music" -o ~/Music/MyFolder/
```

### Adjust Download Speed

```bash
# Fewer workers (slower, less resources)
python cli.py youtube -k "music" -w 4

# More workers (faster, more resources)
python cli.py youtube -k "music" -w 16
```

## Python API Quick Start

### Basic Usage

```python
from media_crawler import CrawlerFactory, ApplicationConfig

# Create configuration
config = ApplicationConfig.for_youtube()

# Create crawler
crawler = CrawlerFactory.create_crawler(
    config=config,
    start_urls=["https://www.youtube.com/watch?v=dQw4w9WgXcQ"]
)

# Start crawling
crawler.crawl()
```

### Custom Configuration

```python
from media_crawler import (
    ApplicationConfig,
    CrawlerConfig,
    DownloadConfig
)

# Configure crawler
config = ApplicationConfig.for_youtube(
    crawler_config=CrawlerConfig(
        max_depth=2,
        max_workers=8
    ),
    download_config=DownloadConfig(
        download_folder="~/Music/Custom/",
        audio_quality="320"
    )
)

# Create and run
crawler = CrawlerFactory.create_crawler(config=config, start_urls=["URL"])
crawler.crawl()
```

## Common Use Cases

### 1. Build a Music Library

```bash
# Download by genre
python cli.py youtube -k "jazz music" -d 2 -o ~/Music/Jazz/
python cli.py youtube -k "classical music" -d 2 -o ~/Music/Classical/
python cli.py youtube -k "electronic music" -d 2 -o ~/Music/Electronic/
```

### 2. Download a Playlist

```bash
python cli.py youtube -u "https://youtube.com/playlist?list=PLxxxxxxxx" -d 1
```

### 3. Archive a Channel

```bash
python cli.py youtube -u "https://youtube.com/@channel-name" -d 2
```

### 4. Discover New Music

```bash
python cli.py soundcloud -u "https://soundcloud.com/discover" -d 2
```

## Understanding Output

While crawling, you'll see:

```
🔍 MEDIA CRAWLER - PROGRESS
======================================================================

Status: Crawling...
Elapsed Time: 00:05:23

──────────────────────────────────────────────────────────────────────
CRAWL PROGRESS
──────────────────────────────────────────────────────────────────────
  Depth: 2 / 2
  URLs Processed: 42
  URLs in Queue: 15
  Links Found: 156

──────────────────────────────────────────────────────────────────────
DOWNLOAD PROGRESS
──────────────────────────────────────────────────────────────────────
  Completed: 38
  Failed: 2
  Success Rate: 95.0%

──────────────────────────────────────────────────────────────────────
CURRENT ACTIVITY
──────────────────────────────────────────────────────────────────────
URL: https://youtube.com/watch?v=example
```

## Files Created

After running, you'll find:

```
~/Music/YouTube/          # Downloaded audio files
youtube.db                # Database tracking downloads
```

## Next Steps

Now that you're set up:

1. **Read the full documentation**: [README.md](../README.md)
2. **Learn advanced features**: [docs/USAGE.md](USAGE.md)
3. **Explore the API**: [docs/API.md](API.md)
4. **Understand architecture**: [docs/ARCHITECTURE.md](ARCHITECTURE.md)

## Troubleshooting

### Issue: ChromeDriver not found

```bash
# Install ChromeDriver
sudo apt install chromium-chromedriver  # Ubuntu/Debian
brew install chromedriver  # macOS

# Or use automatic installer
pip install webdriver-manager
```

### Issue: FFmpeg not found

```bash
# Install FFmpeg
sudo apt install ffmpeg  # Ubuntu/Debian
brew install ffmpeg  # macOS
```

### Issue: Permission denied

```bash
# Create directory with proper permissions
mkdir -p ~/Music/Downloads/
chmod 755 ~/Music/Downloads/
```

### Issue: Downloads fail

```bash
# Try with fewer workers
python cli.py youtube -k "music" -w 2

# Enable verbose logging
python cli.py youtube -k "music" -v
```

## Getting Help

- 📚 **Documentation**: Check [README.md](../README.md) and [docs/](.)
- 🐛 **Issues**: [GitHub Issues](https://github.com/HasanRagab/media-crawler/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/HasanRagab/media-crawler/discussions)
- 📧 **Email**: hasanmragab@gmail.com

## Examples

Check the `examples/` directory for more:

```bash
# Run example scripts
python examples/main.py
python examples/examples.py

# Run diagnostic
python examples/diagnose.py
```

## Tips

### Tip 1: Start Small
```bash
# Test with depth 1 first
python cli.py youtube -k "test" -d 1 -w 2
```

### Tip 2: Use High Quality for Favorites
```bash
python cli.py youtube -k "favorite album" -q 320
```

### Tip 3: Organize by Genre
```bash
python cli.py youtube -k "jazz" -o ~/Music/Jazz/
python cli.py youtube -k "rock" -o ~/Music/Rock/
```

### Tip 4: Check Database
```bash
sqlite3 youtube.db "SELECT COUNT(*) FROM tracks;"
sqlite3 youtube.db "SELECT title FROM tracks LIMIT 10;"
```

## What's Next?

- Try different depth levels
- Experiment with worker counts
- Explore different platforms (SoundCloud)
- Use the Python API for custom workflows
- Check out advanced configuration options

Happy crawling! 🎵✨

---

**Quick Links:**
- [Full Documentation](../README.md)
- [Usage Guide](USAGE.md)
- [API Reference](API.md)
- [Architecture](ARCHITECTURE.md)
- [Contributing](CONTRIBUTING.md)
