"""
Database handler module with proper abstraction and OOP principles.
"""
import sqlite3
import logging
from abc import ABC, abstractmethod
from threading import Lock
from typing import Optional, List, Tuple

from .config import DatabaseConfig
from .exceptions import DatabaseException

logger = logging.getLogger(__name__)


class IDatabase(ABC):
    """Interface for database operations."""
    
    @abstractmethod
    def save_track(self, url: str, title: str) -> None:
        """Save a track to the database."""
        pass
    
    @abstractmethod
    def is_downloaded(self, url: str) -> bool:
        """Check if a track has been downloaded."""
        pass
    
    @abstractmethod
    def mark_downloaded(self, url: str) -> None:
        """Mark a track as downloaded."""
        pass
    
    @abstractmethod
    def get_all_tracks(self) -> List[Tuple[str, str, int, Optional[str]]]:
        """Get all tracks from the database."""
        pass
    
    @abstractmethod
    def get_downloaded_count(self) -> int:
        """Get count of downloaded tracks."""
        pass
    
    @abstractmethod
    def get_pending_count(self) -> int:
        """Get count of pending tracks."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close the database connection."""
        pass


class SQLiteDatabase(IDatabase):
    """SQLite implementation of the database interface."""
    
    def __init__(self, config: DatabaseConfig):
        """
        Initialize SQLite database handler.
        
        Args:
            config: Database configuration object
        """
        self.config = config
        self._lock = Lock()
        self._initialize_connection()
        self._initialize_schema()
    
    def _initialize_connection(self) -> None:
        """Establish database connection."""
        try:
            self._conn = sqlite3.connect(
                self.config.db_path,
                check_same_thread=self.config.check_same_thread
            )
            logger.info(f"Database connection established: {self.config.db_path}")
        except sqlite3.Error as e:
            raise DatabaseException(f"Failed to connect to database: {e}")
    
    def _initialize_schema(self) -> None:
        """Create database tables if they don't exist."""
        try:
            with self._lock, self._conn:
                self._conn.execute('''
                    CREATE TABLE IF NOT EXISTS tracks (
                        url TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        downloaded INTEGER DEFAULT 0,
                        downloaded_at TIMESTAMP
                    )
                ''')
                self._conn.execute(
                    'CREATE INDEX IF NOT EXISTS idx_downloaded ON tracks (downloaded)'
                )
                self._conn.execute(
                    'CREATE INDEX IF NOT EXISTS idx_url ON tracks (url)'
                )
            logger.info("Database schema initialized")
        except sqlite3.Error as e:
            raise DatabaseException(f"Failed to initialize schema: {e}")
    
    def save_track(self, url: str, title: str) -> None:
        """
        Save a track to the database.
        
        Args:
            url: Track URL
            title: Track title
            
        Raises:
            DatabaseException: If save operation fails
        """
        with self._lock:
            try:
                with self._conn:
                    self._conn.execute(
                        'INSERT OR IGNORE INTO tracks (url, title) VALUES (?, ?)',
                        (url, title)
                    )
                logger.debug(f"Track saved: {title}")
            except sqlite3.Error as e:
                raise DatabaseException(f"Failed to save track {url}: {e}")
    
    def is_downloaded(self, url: str) -> bool:
        """
        Check if a track has been downloaded.
        
        Args:
            url: Track URL
            
        Returns:
            True if track is downloaded, False otherwise
        """
        with self._lock:
            try:
                cursor = self._conn.execute(
                    'SELECT downloaded FROM tracks WHERE url = ?',
                    (url,)
                )
                row = cursor.fetchone()
                return bool(row and row[0] == 1)
            except sqlite3.Error as e:
                logger.error(f"Error checking download status for {url}: {e}")
                return False
    
    def mark_downloaded(self, url: str) -> None:
        """
        Mark a track as downloaded.
        
        Args:
            url: Track URL
            
        Raises:
            DatabaseException: If mark operation fails
        """
        with self._lock:
            try:
                with self._conn:
                    self._conn.execute(
                        '''UPDATE tracks 
                           SET downloaded=1, downloaded_at=CURRENT_TIMESTAMP 
                           WHERE url = ?''',
                        (url,)
                    )
                logger.debug(f"Track marked as downloaded: {url}")
            except sqlite3.Error as e:
                raise DatabaseException(f"Failed to mark track as downloaded {url}: {e}")
    
    def get_all_tracks(self) -> List[Tuple[str, str, int, Optional[str]]]:
        """
        Get all tracks from the database.
        
        Returns:
            List of tuples (url, title, downloaded, downloaded_at)
        """
        with self._lock:
            try:
                cursor = self._conn.execute(
                    'SELECT url, title, downloaded, downloaded_at FROM tracks'
                )
                return cursor.fetchall()
            except sqlite3.Error as e:
                raise DatabaseException(f"Failed to retrieve tracks: {e}")
    
    def get_downloaded_count(self) -> int:
        """Get count of downloaded tracks."""
        with self._lock:
            try:
                cursor = self._conn.execute(
                    'SELECT COUNT(*) FROM tracks WHERE downloaded = 1'
                )
                return cursor.fetchone()[0]
            except sqlite3.Error as e:
                logger.error(f"Error getting downloaded count: {e}")
                return 0
    
    def get_pending_count(self) -> int:
        """Get count of pending tracks."""
        with self._lock:
            try:
                cursor = self._conn.execute(
                    'SELECT COUNT(*) FROM tracks WHERE downloaded = 0'
                )
                return cursor.fetchone()[0]
            except sqlite3.Error as e:
                logger.error(f"Error getting pending count: {e}")
                return 0
    
    def close(self) -> None:
        """Close the database connection."""
        if hasattr(self, '_conn') and self._conn:
            self._conn.close()
            logger.info("Database connection closed")


class DatabaseFactory:
    """Factory for creating database instances."""
    
    @staticmethod
    def create_database(config: DatabaseConfig, db_type: str = "sqlite") -> IDatabase:
        """
        Create a database instance based on type.
        
        Args:
            config: Database configuration
            db_type: Type of database (currently only 'sqlite' supported)
            
        Returns:
            Database instance
            
        Raises:
            ValueError: If database type is not supported
        """
        if db_type.lower() == "sqlite":
            return SQLiteDatabase(config)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
