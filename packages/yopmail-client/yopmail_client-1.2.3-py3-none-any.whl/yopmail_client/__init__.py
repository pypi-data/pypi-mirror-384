"""
YOPmail Client Module

A clean, modular client for YOPmail disposable email service.
"""

from .client import YOPMailClient
from .exceptions import (
    YOPMailError,
    MissingTokenError,
    HTTPError,
    CookieSetupError,
    ParseError,
    AuthenticationError
)
from .constants import DEFAULT_CONFIG
from .simple_api import (
    check_inbox,
    get_message_by_id,
    get_last_message,
    get_last_message_content,
    get_inbox_count,
    get_inbox_summary
)

__all__ = [
    # Main client class
    "YOPMailClient",
    
    # Essential functions
    "check_inbox",
    "get_message_by_id", 
    "get_last_message",
    "get_last_message_content",
    "get_inbox_count",
    "get_inbox_summary",
    
    # Exceptions
    "YOPMailError",
    "MissingTokenError", 
    "HTTPError",
    "CookieSetupError",
    "ParseError",
    "AuthenticationError",
    
    # Configuration
    "DEFAULT_CONFIG"
]

__version__ = "1.2.1"
