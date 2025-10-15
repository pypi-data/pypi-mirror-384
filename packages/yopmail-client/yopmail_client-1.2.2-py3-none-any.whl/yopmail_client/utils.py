"""
Utility functions for YOPmail client.

This module contains helper functions for HTML parsing, token extraction,
and other utility operations used throughout the client.
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from bs4 import BeautifulSoup

from .exceptions import ParseError, MissingTokenError
from .constants import SELECTORS

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Structured message object."""
    id: str
    subject: str
    sender: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    
    def __str__(self) -> str:
        return f"Message(id='{self.id}', subject='{self.subject}', sender='{self.sender}')"


class HTMLParser:
    """HTML parsing utilities for YOPmail responses."""
    
    @staticmethod
    def extract_yp_token(html: str) -> str:
        """
        Extract the yp token from HTML response.
        
        Args:
            html: HTML content to parse
            
        Returns:
            Extracted yp token
            
        Raises:
            MissingTokenError: If yp token is not found
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            inp = soup.find("input", {"id": "yp"})
            
            if inp and inp.has_attr("value"):
                token = inp["value"]
                logger.debug(f"YP token extracted: {token[:10]}...")
                return token
            else:
                raise MissingTokenError("yp")
                
        except Exception as e:
            logger.error(f"Failed to extract yp token: {e}")
            raise ParseError("yp token", SELECTORS["yp_token"])
    
    @staticmethod
    def parse_messages(html: str) -> List[Message]:
        """
        Parse messages from inbox HTML.
        
        Args:
            html: HTML content to parse
            
        Returns:
            List of Message objects
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            message_elements = soup.select(SELECTORS["message"])
            messages = []
            
            for element in message_elements:
                message = HTMLParser._parse_single_message(element)
                if message:
                    messages.append(message)
            
            logger.debug(f"Parsed {len(messages)} messages from HTML")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to parse messages: {e}")
            raise ParseError("messages", SELECTORS["message"])
    
    @staticmethod
    def _parse_single_message(element) -> Optional[Message]:
        """Parse a single message element."""
        try:
            # Extract message ID
            message_id = element.get("id", "")
            if not message_id:
                return None
            
            # Extract subject
            subject_elem = element.select_one(SELECTORS["subject"])
            subject = subject_elem.get_text(strip=True) if subject_elem else ""
            
            # Extract sender
            sender_elem = element.select_one(".lmf")
            sender = sender_elem.get_text(strip=True) if sender_elem else None
            
            # Extract time
            time_elem = element.select_one(".lmh")
            time_str = time_elem.get_text(strip=True) if time_elem else None
            
            return Message(
                id=message_id,
                subject=subject,
                sender=sender,
                time=time_str
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse single message: {e}")
            return None


class RequestBuilder:
    """Helper class for building HTTP requests."""
    
    @staticmethod
    def build_inbox_params(login: str, yp_token: str, page: int = 1) -> Dict[str, Any]:
        """
        Build parameters for inbox request.
        
        Args:
            login: Mailbox login name
            yp_token: Authentication token
            page: Page number (default: 1)
            
        Returns:
            Dictionary of request parameters
        """
        from .constants import YJ_TOKEN, VERSION, AD_PARAM
        
        return {
            "login": login,
            "p": page,
            "d": "",
            "ctrl": "",
            "yp": yp_token,
            "yj": YJ_TOKEN,
            "v": VERSION,
            "r_c": "",
            "id": "",
            "ad": AD_PARAM,
        }
    
    @staticmethod
    def build_mail_params(login: str, message_id: str) -> Dict[str, Any]:
        """
        Build parameters for mail request.
        
        Args:
            login: Mailbox login name
            message_id: Message ID (already formatted)
            
        Returns:
            Dictionary of request parameters
        """
        return {
            "b": login,
            "id": message_id,
        }
    
    @staticmethod
    def build_login_data(login: str) -> Dict[str, str]:
        """
        Build data for login request.
        
        Args:
            login: Mailbox login name
            
        Returns:
            Dictionary of login data
        """
        return {"login": login}


def format_message_id(message_id: str) -> str:
    """
    Format message ID for mail endpoint.
    
    Args:
        message_id: Original message ID
        
    Returns:
        Formatted message ID with prefix
    """
    # Check if message ID already has the correct prefix
    if message_id.startswith('me_'):
        return message_id
    elif message_id.startswith('e_'):
        # Remove e_ prefix and add me_ prefix for mail endpoint
        base_id = message_id[2:]  # Remove 'e_' prefix
        return f"me_{base_id}"
    else:
        # Use 'me_' prefix for mail endpoint (like browser does)
        return f"me_{message_id}"


def validate_mailbox_name(mailbox: str) -> bool:
    """
    Validate mailbox name format.
    
    Args:
        mailbox: Mailbox name to validate
        
    Returns:
        True if valid, False otherwise
    """
    import re
    
    # YOPmail mailbox validation regex
    pattern = r'^[-a-zA-Z0-9@_.+]{1,64}$'
    return bool(re.match(pattern, mailbox))


def sanitize_mailbox_name(mailbox: str) -> str:
    """
    Sanitize mailbox name by removing @domain if present.
    
    Args:
        mailbox: Mailbox name to sanitize
        
    Returns:
        Sanitized mailbox name
    """
    if '@' in mailbox:
        mailbox = mailbox.split('@')[0]
    return mailbox.lower()
