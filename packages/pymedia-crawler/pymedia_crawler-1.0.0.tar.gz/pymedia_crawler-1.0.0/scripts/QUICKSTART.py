#!/usr/bin/env python3
"""
Quick Start Guide - Interactive script to help you get started
"""
import os
import sys

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def print_section(text):
    print(f"\n--- {text} ---\n")

print_header("MEDIA CRAWLER - QUICK START GUIDE")

print("""
Welcome to the refactored Media Crawler!

This application allows you to download media content from YouTube, 
SoundCloud, and other platforms with full control over settings.
""")

print_section("Step 1: Installation")
print("""
Make sure you have all dependencies installed:

    pip install -r requirements.txt

You also need ChromeDriver:
- Download from: https://chromedriver.chromium.org/
- Match your Chrome browser version
- Add to PATH or place in project directory
""")

print_section("Step 2: Choose Your Approach")
print("""
There are THREE ways to use this crawler:

1. SIMPLE - Using main.py (pre-configured examples)
2. FLEXIBLE - Using CLI (command-line interface)
3. ADVANCED - Using Python API (full customization)
""")

print_section("Option 1: SIMPLE - Using main.py")
print("""
Edit main.py and uncomment the example you want:

    python main.py

Examples available:
- Simple YouTube search
- Simple SoundCloud crawl
- Custom configuration
- Multi-platform crawling
""")

print_section("Option 2: FLEXIBLE - Using CLI")
print("""
Command-line interface with many options:

YouTube search:
    python cli.py youtube -k "lofi hip hop" -d 2 -w 8

YouTube direct URL:
    python cli.py youtube -u "https://youtube.com/@channel" -d 1

SoundCloud:
    python cli.py soundcloud -u "https://soundcloud.com/discover" -d 3

Custom quality:
    python cli.py youtube -k "jazz" -q 320 -o ~/Music/Jazz/

See all options:
    python cli.py --help
""")

print_section("Option 3: ADVANCED - Using Python API")
print("""
Full control by writing Python code:

    from factory import CrawlerFactory
    from config import ApplicationConfig, CrawlerConfig
    
    # Simple
    crawler = CrawlerFactory.create_youtube_crawler(['url'], max_depth=2)
    crawler.crawl()
    crawler.close()
    
    # Advanced
    config = ApplicationConfig.for_youtube(
        crawler_config=CrawlerConfig(max_depth=3, max_workers=16)
    )
    crawler = CrawlerFactory.create_crawler(config, ['url'])
    crawler.crawl()
    
See examples.py for more:
    python examples.py
""")

print_section("Quick Test")
print("""
Try this quick test to make sure everything works:

    python3 -c "from factory import CrawlerFactory; print('✓ Installation OK!')"

If no errors, you're ready to go!
""")

print_section("Common Tasks")
print("""
Resume interrupted crawl:
    Just run the same command again - state is automatically saved!

Clear saved state:
    python cli.py youtube -k "music" --clear-state

Change download location:
    python cli.py youtube -k "music" -o ~/MyMusic/

High quality downloads:
    python cli.py youtube -k "music" -q 320 -f mp3

More parallel downloads:
    python cli.py youtube -k "music" -w 20

Debug mode (see browser):
    python cli.py youtube -k "music" --no-headless -v
""")

print_section("Configuration")
print("""
You can customize everything:
- Crawl depth and breadth
- Download quality and format
- Output folder
- Database location
- Retry strategy
- Scroll behavior
- Platform-specific settings

See README.md for full configuration options.
See config.py for all available settings.
""")

print_section("Troubleshooting")
print("""
ChromeDriver not found:
    - Download matching your Chrome version
    - Add to PATH or project directory
    
Connection errors:
    - Check internet connection
    - Increase retry attempts
    - Use VPN if region-blocked
    
Memory issues:
    - Reduce max_workers
    - Reduce max_depth
    - Close other applications
    
Import errors:
    - pip install -r requirements.txt
    - Check Python version (3.8+)
""")

print_section("Next Steps")
print("""
1. Run a simple example:
       python main.py

2. Try the CLI:
       python cli.py youtube -k "test" -d 1

3. Check examples:
       python examples.py

4. Read the docs:
       README.md - User guide
       REFACTORING_SUMMARY.md - Technical details
       
5. Customize:
       Edit config.py for your needs
       Add new platforms (see README.md)
""")

print_section("Support")
print("""
For help:
- Check README.md
- Review examples.py
- Read inline documentation (docstrings)
- Check error messages carefully

The code is well-documented with type hints and docstrings.
Use your IDE's autocomplete to explore available options!
""")

print_header("Ready to Start!")
print("""
Pick your preferred method and start crawling!

Simple start:
    python cli.py youtube -k "music" -d 1

Enjoy! 🎵
""")
