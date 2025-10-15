import os
import time
import sqlite3
import logging
import json
import random
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from yt_dlp import YoutubeDL
from threading import Lock
from urllib.error import HTTPError
import urllib3

DB_PATH = 'soundcloud.db'
STATE_PATH = 'crawler_state.json'
DOWNLOAD_FOLDER = os.path.expanduser('~/Music/SoundCloud/')
MAX_WORKERS = 8
SCROLL_PAUSE = 0.5
SCROLL_COUNT = 10
BASE_DOMAIN = 'soundcloud.com'
IGNORE_WORDS = ['pages', 'cookies', 'page', 'charts', 'followers', 'you', 'your', 'library', 'directory', 'people', 'tag', 'tags']

logging.basicConfig(format='%(asctime)s | %(levelname)s | %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

db_lock = Lock()  # Serialize DB writes

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # seconds

class SoundcloudCrawler:
    def __init__(self, db_handler, max_depth=3, download_folder=DOWNLOAD_FOLDER, state_path=STATE_PATH):
        self.db = db_handler
        self.max_depth = max_depth
        self.download_folder = download_folder
        self.state_path = state_path
        os.makedirs(download_folder, exist_ok=True)
        self.driver = self._init_driver()

        self.queue = []
        self.visited = set()
        self._load_state()

    def _init_driver(self):
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--log-level=3')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        return webdriver.Chrome(options=options)

    def _save_state(self):
        try:
            with open(self.state_path, 'w') as f:
                json.dump({
                    'queue': self.queue,
                    'visited': list(self.visited)
                }, f)
            logger.info(f"Saved crawler state: {len(self.queue)} URLs in queue, {len(self.visited)} visited")
        except Exception as e:
            logger.error(f"Failed to save crawler state: {e}")

    def _load_state(self):
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, 'r') as f:
                    data = json.load(f)
                    self.queue = data.get('queue', [])
                    self.visited = set(data.get('visited', []))
                logger.info(f"Loaded crawler state: {len(self.queue)} URLs in queue, {len(self.visited)} visited")
            except Exception as e:
                logger.error(f"Failed to load crawler state: {e}")
                self.queue = []
                self.visited = set()

    def close(self):
        self.driver.quit()
        self._save_state()

    def scroll_page(self, url, scroll_count=SCROLL_COUNT, pause=SCROLL_PAUSE):
        logger.info(f'Loading and scrolling: {url}')
        return scroll_page_with_retry(self.driver, url, scroll_count, pause)

    def is_valid_track_url(self, href):
        if not href:
            return False
        url = urljoin(f'https://{BASE_DOMAIN}', href) if href.startswith('/') else href
        if not url.startswith('http'):
            return False
        parsed = urlparse(url)
        if BASE_DOMAIN not in parsed.netloc:
            return False
        parts = [p for p in parsed.path.split('/') if p]
        if not parts or len(parts) != 2:
            return False
        if 'user-' in parts[0]:
            return False
        if any(ignored in url.lower() for ignored in IGNORE_WORDS):
            return False
        return url

    def extract_links(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        for a in soup.find_all('a', href=True):
            url = self.is_valid_track_url(a['href'])
            if url and not self.db.is_downloaded(url):
                links.add(url)
        return links

    def extract_all_internal_links(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            url = urljoin(f'https://{BASE_DOMAIN}', href) if href.startswith('/') else href
            parsed = urlparse(url)
            if BASE_DOMAIN in parsed.netloc:
                clean_url = parsed.scheme + '://' + parsed.netloc + parsed.path
                if any(ignored in clean_url.lower() for ignored in IGNORE_WORDS):
                    continue
                links.add(clean_url)
        return links

    def crawl(self):
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            while self.queue:
                current_url, depth = self.queue.pop(0)
                if current_url in self.visited or depth > self.max_depth:
                    continue

                logger.info(f'Crawling depth {depth}: {current_url}')
                self.visited.add(current_url)

                html = self.scroll_page(current_url)
                if not html:
                    continue

                track_links = self.extract_links(html)
                logger.info(f"[Depth {depth}] Found {len(track_links)} track(s)")

                futures = {
                    executor.submit(download_track, url, i + 1, len(track_links), self.download_folder): url
                    for i, url in enumerate(track_links)
                }

                for future in as_completed(futures):
                    try:
                        res = future.result()
                        if res:
                            url, title = res
                            self.db.save_track(url, title)
                            self.db.mark_downloaded(url)
                    except Exception as e:
                        logger.error(f"Error in download future: {e}")

                all_links = self.extract_all_internal_links(html)
                for link in all_links:
                    if link not in self.visited and (link, depth + 1) not in self.queue:
                        self.queue.append((link, depth + 1))

                self._save_state()

