"""
Custom exceptions for YOPmail client.

This module defines all custom exceptions used throughout the YOPmail client
for better error handling and debugging.
"""

from typing import Optional


class YOPMailError(Exception):
    """Base exception for all YOPmail client errors."""
    
    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class MissingTokenError(YOPMailError):
    """Raised when required authentication token is missing."""
    
    def __init__(self, token_name: str):
        message = f"Required token '{token_name}' is missing"
        super().__init__(message)


class HTTPError(YOPMailError):
    """Raised when HTTP request fails."""
    
    def __init__(self, status_code: int, url: str, response_text: str = ""):
        self.status_code = status_code
        self.url = url
        self.response_text = response_text
        message = f"HTTP {status_code} error for {url}"
        super().__init__(message, response_text)


class CookieSetupError(YOPMailError):
    """Raised when cookie setup fails."""
    
    def __init__(self, cookie_name: str, reason: str = ""):
        message = f"Failed to set cookie '{cookie_name}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class ParseError(YOPMailError):
    """Raised when HTML parsing fails."""
    
    def __init__(self, element: str, selector: str = ""):
        message = f"Failed to parse element '{element}'"
        if selector:
            message += f" with selector '{selector}'"
        super().__init__(message)


class AuthenticationError(YOPMailError):
    """Raised when authentication fails."""
    
    def __init__(self, reason: str = "Authentication failed"):
        super().__init__(reason)


class NetworkError(YOPMailError):
    """Raised when network operation fails."""
    
    def __init__(self, operation: str, reason: str = ""):
        message = f"Network error during {operation}"
        if reason:
            message += f": {reason}"
        super().__init__(message)
