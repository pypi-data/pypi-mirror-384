"""
Link extraction strategies for different platforms.
"""
import logging
from abc import ABC, abstractmethod
from typing import Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from .config import PlatformConfig
from .database import IDatabase

logger = logging.getLogger(__name__)


class ILinkExtractor(ABC):
    """Interface for link extraction strategies."""
    
    @abstractmethod
    def extract_content_links(self, html: str) -> Set[str]:
        """Extract links to downloadable content (videos, tracks, etc.)."""
        pass
    
    @abstractmethod
    def extract_navigation_links(self, html: str) -> Set[str]:
        """Extract links for further crawling."""
        pass


class BaseLinkExtractor(ILinkExtractor):
    """Base class for link extractors with common functionality."""
    
    def __init__(self, platform_config: PlatformConfig, database: IDatabase):
        """
        Initialize base link extractor.
        
        Args:
            platform_config: Platform configuration
            database: Database handler
        """
        self.platform_config = platform_config
        self.database = database
    
    def _is_valid_domain(self, url: str) -> bool:
        """Check if URL belongs to the platform domain."""
        parsed = urlparse(url)
        return self.platform_config.base_domain in parsed.netloc
    
    def _should_ignore(self, url: str) -> bool:
        """Check if URL should be ignored based on ignore words."""
        url_lower = url.lower()
        return any(word in url_lower for word in self.platform_config.ignore_words)
    
    def _parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content."""
        return BeautifulSoup(html, 'html.parser')


class YouTubeLinkExtractor(BaseLinkExtractor):
    """Link extractor for YouTube platform."""
    
    def extract_content_links(self, html: str) -> Set[str]:
        """
        Extract YouTube video links.
        
        Args:
            html: HTML content
            
        Returns:
            Set of video URLs
        """
        soup = self._parse_html(html)
        links = set()
        
        for a in soup.find_all('a', href=True):
            href = a.get('href')
            if not href or not isinstance(href, str):
                continue
            if '/watch?v=' in href:
                # Extract just the video URL without extra parameters
                full_url = urljoin(self.platform_config.base_url, href.split('&')[0])
                if not self.database.is_downloaded(full_url):
                    links.add(full_url)
        
        logger.debug(f"Extracted {len(links)} YouTube video links")
        return links
    
    def extract_navigation_links(self, html: str) -> Set[str]:
        """
        Extract YouTube navigation links for further crawling.
        
        Args:
            html: HTML content
            
        Returns:
            Set of navigation URLs
        """
        soup = self._parse_html(html)
        links = set()
        
        for a in soup.find_all('a', href=True):
            href = a.get('href')
            if not href or not isinstance(href, str):
                continue
            # Look for channel, playlist, and search result links
            if href.startswith('/') and not href.startswith('/watch'):
                full_url = urljoin(self.platform_config.base_url, href)
                if not self._should_ignore(full_url):
                    links.add(full_url)
        
        logger.debug(f"Extracted {len(links)} YouTube navigation links")
        return links


class SoundCloudLinkExtractor(BaseLinkExtractor):
    """Link extractor for SoundCloud platform."""
    
    def _is_valid_track_url(self, href: str) -> str:
        """
        Validate and normalize a SoundCloud track URL.
        
        Args:
            href: URL or path
            
        Returns:
            Normalized URL if valid, empty string otherwise
        """
        if not href:
            return ""
        
        # Normalize to full URL
        url = urljoin(self.platform_config.base_url, href) if href.startswith('/') else href
        
        if not url.startswith('http'):
            return ""
        
        if not self._is_valid_domain(url):
            return ""
        
        parsed = urlparse(url)
        parts = [p for p in parsed.path.split('/') if p]
        
        # Valid track URLs have exactly 2 parts: /artist/track
        if not parts or len(parts) != 2:
            return ""
        
        # Ignore user- prefixed URLs
        if 'user-' in parts[0]:
            return ""
        
        if self._should_ignore(url):
            return ""
        
        return url
    
    def extract_content_links(self, html: str) -> Set[str]:
        """
        Extract SoundCloud track links.
        
        Args:
            html: HTML content
            
        Returns:
            Set of track URLs
        """
        soup = self._parse_html(html)
        links = set()
        
        for a in soup.find_all('a', href=True):
            href = a.get('href')
            if not href or not isinstance(href, str):
                continue
            url = self._is_valid_track_url(href)
            if url and not self.database.is_downloaded(url):
                links.add(url)
        
        logger.debug(f"Extracted {len(links)} SoundCloud track links")
        return links
    
    def extract_navigation_links(self, html: str) -> Set[str]:
        """
        Extract SoundCloud navigation links for further crawling.
        
        Args:
            html: HTML content
            
        Returns:
            Set of navigation URLs
        """
        soup = self._parse_html(html)
        links = set()
        
        for a in soup.find_all('a', href=True):
            href = a.get('href')
            if not href or not isinstance(href, str):
                continue
            url = urljoin(self.platform_config.base_url, href) if href.startswith('/') else href
            
            if not self._is_valid_domain(url):
                continue
            
            parsed = urlparse(url)
            clean_url = parsed.scheme + '://' + parsed.netloc + parsed.path
            
            if self._should_ignore(clean_url):
                continue
            
            links.add(clean_url)
        
        logger.debug(f"Extracted {len(links)} SoundCloud navigation links")
        return links


class LinkExtractorFactory:
    """Factory for creating link extractor instances."""
    
    @staticmethod
    def create_extractor(
        platform_config: PlatformConfig,
        database: IDatabase
    ) -> ILinkExtractor:
        """
        Create a link extractor based on platform.
        
        Args:
            platform_config: Platform configuration
            database: Database handler
            
        Returns:
            Link extractor instance
            
        Raises:
            ValueError: If platform is not supported
        """
        platform_name = platform_config.name.lower()
        
        if platform_name == "youtube":
            return YouTubeLinkExtractor(platform_config, database)
        elif platform_name == "soundcloud":
            return SoundCloudLinkExtractor(platform_config, database)
        else:
            raise ValueError(f"Unsupported platform: {platform_config.name}")
