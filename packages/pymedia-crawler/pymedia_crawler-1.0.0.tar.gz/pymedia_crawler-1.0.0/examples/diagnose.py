#!/usr/bin/env python3
"""
Diagnostic script to test ChromeDriver installation and configuration.
"""
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

def test_chromedriver():
    """Test if ChromeDriver is properly installed and accessible."""
    
    logger.info("Step 1: Testing ChromeDriver availability...")
    try:
        from selenium import webdriver
        logger.info("✓ Selenium is installed")
    except ImportError as e:
        logger.error("✗ Selenium not installed. Run: pip install selenium")
        return False
    
    logger.info("\nStep 2: Testing Chrome options...")
    try:
        from selenium.webdriver.chrome.options import Options
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        logger.info("✓ Chrome options configured")
    except Exception as e:
        logger.error(f"✗ Failed to configure Chrome options: {e}")
        return False
    
    logger.info("\nStep 3: Attempting to start ChromeDriver...")
    logger.info("(This may take 10-30 seconds on first run)")
    try:
        driver = webdriver.Chrome(options=options)
        logger.info("✓ ChromeDriver started successfully!")
        
        logger.info("\nStep 4: Testing page load...")
        driver.get("https://www.google.com")
        logger.info(f"✓ Page loaded: {driver.title}")
        
        driver.quit()
        logger.info("✓ ChromeDriver closed successfully")
        
        logger.info("\n" + "="*60)
        logger.info("SUCCESS! ChromeDriver is working correctly")
        logger.info("="*60)
        return True
        
    except Exception as e:
        logger.error(f"\n✗ ChromeDriver failed to start: {e}")
        logger.error("\nPossible solutions:")
        logger.error("1. Install ChromeDriver:")
        logger.error("   - Visit: https://chromedriver.chromium.org/downloads")
        logger.error("   - Download version matching your Chrome browser")
        logger.error("   - Add to PATH or place in project directory")
        logger.error("\n2. Check Chrome browser is installed:")
        logger.error("   - ChromeDriver requires Chrome or Chromium browser")
        logger.error("\n3. On Linux, you may need:")
        logger.error("   - sudo apt install chromium-browser chromium-chromedriver")
        logger.error("   - or: sudo apt install google-chrome-stable")
        logger.error("\n4. Try non-headless mode (see browser window):")
        logger.error("   - Edit the script and remove '--headless' option")
        return False

def test_imports():
    """Test if all required modules can be imported."""
    logger.info("\nTesting project imports...")
    
    modules = [
        'config',
        'database', 
        'webdriver',
        'downloader',
        'link_extractor',
        'crawler',
        'factory',
        'exceptions',
        'utils',
        'state_manager'
    ]
    
    all_ok = True
    for module in modules:
        try:
            __import__(module)
            logger.info(f"  ✓ {module}")
        except Exception as e:
            logger.error(f"  ✗ {module}: {e}")
            all_ok = False
    
    return all_ok

if __name__ == '__main__':
    logger.info("="*60)
    logger.info("MEDIA CRAWLER - DIAGNOSTIC TOOL")
    logger.info("="*60)
    
    # Test imports
    imports_ok = test_imports()
    
    if not imports_ok:
        logger.error("\n⚠ Some imports failed. Fix import errors before continuing.")
        sys.exit(1)
    
    logger.info("\n✓ All imports successful\n")
    logger.info("="*60)
    
    # Test ChromeDriver
    chrome_ok = test_chromedriver()
    
    if chrome_ok:
        logger.info("\nYou're all set! Try running:")
        logger.info("  python cli.py youtube -k 'test' -d 1")
        sys.exit(0)
    else:
        logger.error("\n⚠ ChromeDriver test failed. Please fix the issues above.")
        sys.exit(1)
