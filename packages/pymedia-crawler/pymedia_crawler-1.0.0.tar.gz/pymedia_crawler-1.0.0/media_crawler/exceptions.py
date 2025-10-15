"""
Custom exceptions for the crawler application.
"""


class CrawlerException(Exception):
    """Base exception for all crawler-related errors."""
    pass


class DatabaseException(CrawlerException):
    """Exception raised for database-related errors."""
    pass


class DownloadException(CrawlerException):
    """Exception raised for download-related errors."""
    pass


class NetworkException(CrawlerException):
    """Exception raised for network-related errors."""
    pass


class ConfigurationException(CrawlerException):
    """Exception raised for configuration-related errors."""
    pass


class ValidationException(CrawlerException):
    """Exception raised for validation errors."""
    pass
