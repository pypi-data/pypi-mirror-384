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

DB_PATH = 'youtube.db'
STATE_PATH = 'crawler_state.json'
DOWNLOAD_FOLDER = os.path.expanduser('~/Music/YouTube/')
MAX_WORKERS = 8
SCROLL_PAUSE = 0.5
SCROLL_COUNT = 10
BASE_DOMAIN = 'youtube.com'
IGNORE_WORDS = ['pages', 'cookies', 'page', 'charts', 'followers', 'you', 'your', 'library', 'directory', 'people', 'tag', 'tags']

logging.basicConfig(format='%(asctime)s | %(levelname)s | %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

db_lock = Lock()  # Serialize DB writes

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # seconds


def retry_sleep(attempt):
    sleep_time = (RETRY_BACKOFF_BASE ** attempt) + random.uniform(0, 1)
    logger.info(f"Retry sleeping for {sleep_time:.1f}s")
    time.sleep(sleep_time)

class YouTubeCrawler:
    def __init__(self, db_handler, start_urls, max_depth=2, download_folder=DOWNLOAD_FOLDER, state_path=STATE_PATH):
        self.db = db_handler
        self.queue = [(url, 0) for url in start_urls]
        self.visited = set()
        self.max_depth = max_depth
        self.download_folder = download_folder
        self.state_path = state_path
        os.makedirs(download_folder, exist_ok=True)
        self.driver = self._init_driver()
        self._load_state()

    def _init_driver(self):
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--log-level=3')
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

    def scroll_page(self, url, scroll_count=10, pause=2):
        return scroll_page_with_retry(self.driver, url, scroll_count, pause)

    def extract_video_links(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/watch?v=' in href:
                full_url = urljoin("https://www.youtube.com", href.split('&')[0])
                if not self.db.is_downloaded(full_url):
                    links.add(full_url)
        return links

    def extract_internal_links(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        links = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('/') and not href.startswith('/watch'):
                full_url = urljoin("https://www.youtube.com", href)
                links.add(full_url)
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

                video_links = self.extract_video_links(html)
                logger.info(f"[Depth {depth}] Found {len(video_links)} video(s)")

                futures = {
                    executor.submit(download_track, url, i + 1, len(video_links), self.download_folder): url
                    for i, url in enumerate(video_links)
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

                internal_links = self.extract_internal_links(html)
                for link in internal_links:
                    if link not in self.visited and (link, depth + 1) not in self.queue:
                        self.queue.append((link, depth + 1))

                self._save_state()

class DBHandler:
    def __init__(self, db_path=DB_PATH):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_tables()

    def _init_tables(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS tracks (
                    url TEXT PRIMARY KEY,
                    title TEXT,
                    downloaded INTEGER DEFAULT 0,
                    downloaded_at TIMESTAMP
                )
            ''')
            self.conn.execute('CREATE INDEX IF NOT EXISTS idx_downloaded ON tracks (downloaded)')

    def save_track(self, url, title):
        with db_lock:
            try:
                with self.conn:
                    self.conn.execute('INSERT OR IGNORE INTO tracks (url, title) VALUES (?, ?)', (url, title))
            except Exception as e:
                logger.error(f"DB save_track error for {url}: {e}")

    def is_downloaded(self, url):
        with db_lock:
            try:
                cur = self.conn.execute('SELECT downloaded FROM tracks WHERE url = ?', (url,))
                row = cur.fetchone()
                return row and row[0] == 1
            except Exception as e:
                logger.error(f"DB is_downloaded error for {url}: {e}")
                return False

    def mark_downloaded(self, url):
        with db_lock:
            try:
                with self.conn:
                    self.conn.execute('UPDATE tracks SET downloaded=1, downloaded_at=CURRENT_TIMESTAMP WHERE url = ?', (url,))
            except Exception as e:
                logger.error(f"DB mark_downloaded error for {url}: {e}")


def safe_ytdl_extract_info(ydl, url):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return ydl.extract_info(url, download=False)
        except HTTPError as e:
            if e.code == 404:
                logger.warning(f"HTTP 404 Not Found for {url}, skipping.")
                return None
            logger.error(f"HTTP error {e.code} for {url}, attempt {attempt}")
        except (urllib3.exceptions.ConnectTimeoutError, urllib3.exceptions.MaxRetryError,
                urllib3.exceptions.ReadTimeoutError, urllib3.exceptions.NewConnectionError,
                urllib3.exceptions.ProtocolError) as e:
            logger.error(f"Network error {e} for {url}, attempt {attempt}")
        except Exception as e:
            logger.error(f"Unexpected error extracting info for {url}: {e}, attempt {attempt}")

        if attempt < MAX_RETRIES:
            retry_sleep(attempt)
    return None


def safe_ytdl_download(ydl, url):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            ydl.download([url])
            return True
        except (urllib3.exceptions.ConnectTimeoutError, urllib3.exceptions.MaxRetryError,
                urllib3.exceptions.ReadTimeoutError, urllib3.exceptions.NewConnectionError,
                urllib3.exceptions.ProtocolError) as e:
            logger.error(f"Network error during download {e} for {url}, attempt {attempt}")
        except Exception as e:
            logger.error(f"Unexpected error during download {url}: {e}, attempt {attempt}")

        if attempt < MAX_RETRIES:
            retry_sleep(attempt)
    return False


def scroll_page_with_retry(driver, url, scroll_count=SCROLL_COUNT, pause=SCROLL_PAUSE):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            driver.get(url)
            body = driver.find_element(By.TAG_NAME, 'body')
            for _ in range(scroll_count):
                body.send_keys(Keys.END)
                time.sleep(pause)
            return driver.page_source
        except Exception as e:
            logger.error(f"Error loading {url}, attempt {attempt}: {e}")
        if attempt < MAX_RETRIES:
            retry_sleep(attempt)
    return ''


def download_track(url, idx, total, download_folder):
    logger.info(f"[{idx}/{total}] Processing: {url}")

    ydl_opts_info = {'quiet': True, 'no_warnings': True, 'nocheckcertificate': True}
    title = None
    try:
        with YoutubeDL(ydl_opts_info) as ydl:
            info = safe_ytdl_extract_info(ydl, url)
            if info is None:
                logger.warning(f"[{idx}/{total}] Could not get info, skipping {url}")
                return None
            title = info.get('title', None)
    except Exception as e:
        logger.error(f"[{idx}/{total}] Failed to fetch info for {url}: {e}")
        return None

    if not title:
        logger.warning(f"[{idx}/{total}] Could not get title, skipping {url}")
        return None

    filename = os.path.join(download_folder, f"{title}.mp3")
    if os.path.exists(filename):
        logger.info(f"[{idx}/{total}] File exists, skipping download: {filename}")
        return url, title

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'nocheckcertificate': True,
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/114.0.0.0 Safari/537.36'
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            success = safe_ytdl_download(ydl, url)
            if success:
                logger.info(f"[{idx}/{total}] Finished: {title}")
                return url, title
            else:
                logger.error(f"[{idx}/{total}] Failed to download {url} after retries")
                return None
    except Exception as e:
        logger.error(f"[{idx}/{total}] Failed to download {url}: {str(e)}")
        return None


def crawl_single_start_url(start_url:str, max_depth:int):
    db = DBHandler()
    crawler = YouTubeCrawler(db_handler=db, start_urls=[start_url], max_depth=max_depth, state_path=f"state_{url_to_filename(start_url)}.json")
    try:
        crawler.crawl()
    finally:
        crawler.close()


def url_to_filename(url):
    return url.replace('https://', '').replace('/', '_').replace('?', '_').replace('&', '_').replace('=', '_')


if __name__ == '__main__':

    keywords = ['nf']

    start_urls = [f'https://youtube.com/results?search_query={kw}' for kw in keywords]

    for url in start_urls:
        logger.info(f"Starting crawl for: {url}")
        crawl_single_start_url(url, max_depth=3)