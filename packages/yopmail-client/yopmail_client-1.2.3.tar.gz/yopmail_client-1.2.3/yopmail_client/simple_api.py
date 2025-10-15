"""
Simplified API for YOPmail Client.

This module provides the essential functions needed for YOPmail operations:
1. Check inbox (input: name)
2. Get message by mail ID (input: mail_id) 
3. Get last mail message (input: name)
"""

from typing import List, Optional, Dict, Any
from .client import YOPMailClient
from .utils import Message
from .exceptions import YOPMailError, HTTPError, AuthenticationError


def check_inbox(mailbox_name: str, config: Optional[Dict[str, Any]] = None) -> List[Message]:
    """
    Check inbox for a given mailbox name.
    
    Args:
        mailbox_name: Name of the mailbox (without @yopmail.com)
        config: Optional configuration dictionary for rate limiting and proxy
        
    Returns:
        List of Message objects from the inbox
        
    Raises:
        YOPMailError: If inbox access fails
        HTTPError: If network request fails
        AuthenticationError: If authentication fails
        
    Example:
        >>> messages = check_inbox("testuser")
        >>> for msg in messages:
        ...     print(f"Subject: {msg.subject}")
        
        >>> # With rate limiting and proxy
        >>> config = {"rate_limit_detection": True, "proxy_url": "http://proxy:8080"}
        >>> messages = check_inbox("testuser", config)
    """
    try:
        with YOPMailClient(mailbox_name, config=config) as client:
            client.open_inbox()
            return client.list_messages()
    except Exception as e:
        raise YOPMailError(f"Failed to check inbox for {mailbox_name}: {e}")


def get_message_by_id(mailbox_name: str, message_id: str, config: Optional[Dict[str, Any]] = None) -> str:
    """
    Get message content by message ID.
    
    Args:
        mailbox_name: Name of the mailbox (without @yopmail.com)
        message_id: ID of the message to fetch
        config: Optional configuration dictionary for rate limiting and proxy
        
    Returns:
        Email message body content (text only)
        
    Raises:
        YOPMailError: If message fetch fails
        HTTPError: If network request fails
        AuthenticationError: If authentication fails
        
    Example:
        >>> content = get_message_by_id("testuser", "e_ZwHkZQRlZwZjAQD4ZQNjBGRlZGZ1Zt==")
        >>> print(content)
    """
    try:
        with YOPMailClient(mailbox_name, config=config) as client:
            client.open_inbox()
            return client.fetch_message(message_id)
    except Exception as e:
        raise YOPMailError(f"Failed to get message {message_id} for {mailbox_name}: {e}")


def get_last_message(mailbox_name: str, config: Optional[Dict[str, Any]] = None) -> Optional[Message]:
    """
    Get the most recent message from inbox.
    
    Args:
        mailbox_name: Name of the mailbox (without @yopmail.com)
        
    Returns:
        Most recent Message object, or None if inbox is empty
        
    Raises:
        YOPMailError: If inbox access fails
        HTTPError: If network request fails
        AuthenticationError: If authentication fails
        
    Example:
        >>> last_msg = get_last_message("testuser")
        >>> if last_msg:
        ...     print(f"Latest: {last_msg.subject}")
    """
    try:
        with YOPMailClient(mailbox_name, config=config) as client:
            client.open_inbox()
            messages = client.list_messages()
            return messages[0] if messages else None
    except Exception as e:
        raise YOPMailError(f"Failed to get last message for {mailbox_name}: {e}")


def get_last_message_content(mailbox_name: str, config: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Get the content of the most recent message from inbox.
    
    Args:
        mailbox_name: Name of the mailbox (without @yopmail.com)
        
    Returns:
        Content of the most recent message, or None if inbox is empty
        
    Raises:
        YOPMailError: If inbox access fails
        HTTPError: If network request fails
        AuthenticationError: If authentication fails
        
    Example:
        >>> content = get_last_message_content("testuser")
        >>> if content:
        ...     print(f"Latest message: {content}")
    """
    try:
        with YOPMailClient(mailbox_name, config=config) as client:
            client.open_inbox()
            messages = client.list_messages()
            if messages:
                return client.fetch_message(messages[0].id)
            return None
    except Exception as e:
        raise YOPMailError(f"Failed to get last message content for {mailbox_name}: {e}")


def get_inbox_count(mailbox_name: str, config: Optional[Dict[str, Any]] = None) -> int:
    """
    Get the number of messages in inbox.
    
    Args:
        mailbox_name: Name of the mailbox (without @yopmail.com)
        
    Returns:
        Number of messages in the inbox
        
    Raises:
        YOPMailError: If inbox access fails
        HTTPError: If network request fails
        AuthenticationError: If authentication fails
        
    Example:
        >>> count = get_inbox_count("testuser")
        >>> print(f"Inbox has {count} messages")
    """
    try:
        with YOPMailClient(mailbox_name, config=config) as client:
            client.open_inbox()
            messages = client.list_messages()
            return len(messages)
    except Exception as e:
        raise YOPMailError(f"Failed to get inbox count for {mailbox_name}: {e}")


def get_inbox_summary(mailbox_name: str, config: Optional[Dict[str, Any]] = None) -> dict:
    """
    Get a summary of the inbox.
    
    Args:
        mailbox_name: Name of the mailbox (without @yopmail.com)
        
    Returns:
        Dictionary with inbox summary information
        
    Raises:
        YOPMailError: If inbox access fails
        HTTPError: If network request fails
        AuthenticationError: If authentication fails
        
    Example:
        >>> summary = get_inbox_summary("testuser")
        >>> print(f"Mailbox: {summary['mailbox']}")
        >>> print(f"Messages: {summary['count']}")
    """
    try:
        with YOPMailClient(mailbox_name, config=config) as client:
            client.open_inbox()
            messages = client.list_messages()
            
            return {
                "mailbox": mailbox_name,
                "count": len(messages),
                "has_messages": len(messages) > 0,
                "latest_subject": messages[0].subject if messages else None,
                "latest_sender": messages[0].sender if messages else None,
                "latest_time": messages[0].time if messages else None
            }
    except Exception as e:
        raise YOPMailError(f"Failed to get inbox summary for {mailbox_name}: {e}")
