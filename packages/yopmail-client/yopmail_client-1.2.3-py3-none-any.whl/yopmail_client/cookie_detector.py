"""
Dynamic cookie detection and refresh system.

This module handles automatic detection of expired cookies and
dynamic extraction of fresh authentication tokens from YOPmail responses.
"""

import time
import logging
import re
from typing import Dict, Optional, Tuple, Any
from bs4 import BeautifulSoup
from dataclasses import dataclass

from .exceptions import CookieSetupError, AuthenticationError
from .utils import HTMLParser

logger = logging.getLogger(__name__)


@dataclass
class CookieState:
    """Represents the current state of authentication cookies."""
    ytime: str
    ywm: str
    yc: Optional[str] = None
    yses: Optional[str] = None
    yp_token: Optional[str] = None
    last_updated: float = 0
    
    def is_expired(self, max_age: int = 300) -> bool:
        """Check if cookies are expired based on age."""
        return time.time() - self.last_updated > max_age


class CookieDetector:
    """Detects and refreshes authentication cookies dynamically."""
    
    def __init__(self, client):
        """Initialize cookie detector with HTTP client."""
        self.client = client
        self.cookie_state = CookieState(
            ytime=time.strftime("%H:%M"),
            ywm="",
            last_updated=time.time()
        )
    
    def detect_cookies_from_response(self, response_text: str) -> Dict[str, str]:
        """
        Extract cookies from HTTP response headers and HTML content.
        
        Args:
            response_text: HTML response content
            
        Returns:
            Dictionary of detected cookies
        """
        detected_cookies = {}
        
        try:
            # Extract yp token from HTML
            yp_token = self._extract_yp_token(response_text)
            if yp_token:
                detected_cookies['yp_token'] = yp_token
                logger.debug(f"Detected yp token: {yp_token[:10]}...")
            
            # Extract other tokens from JavaScript or HTML
            yc_token = self._extract_yc_token(response_text)
            if yc_token:
                detected_cookies['yc'] = yc_token
                logger.debug(f"Detected yc token: {yc_token[:10]}...")
            
            yses_token = self._extract_yses_token(response_text)
            if yses_token:
                detected_cookies['yses'] = yses_token
                logger.debug(f"Detected yses token: {yses_token[:10]}...")
            
            return detected_cookies
            
        except Exception as e:
            logger.warning(f"Failed to detect cookies from response: {e}")
            return {}
    
    def _extract_yp_token(self, html: str) -> Optional[str]:
        """Extract yp token from HTML."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            inp = soup.find("input", {"id": "yp"})
            if inp and inp.has_attr("value"):
                return inp["value"]
        except Exception as e:
            logger.debug(f"Failed to extract yp token: {e}")
        return None
    
    def _extract_yc_token(self, html: str) -> Optional[str]:
        """Extract yc token from JavaScript or HTML."""
        try:
            # Look for yc token in JavaScript
            yc_pattern = r'yc["\']?\s*[:=]\s*["\']([^"\']+)["\']'
            match = re.search(yc_pattern, html, re.IGNORECASE)
            if match:
                return match.group(1)
            
            # Look for yc in cookie setting JavaScript
            cookie_pattern = r'cookies?\.set\(["\']yc["\'],\s*["\']([^"\']+)["\']'
            match = re.search(cookie_pattern, html, re.IGNORECASE)
            if match:
                return match.group(1)
                
        except Exception as e:
            logger.debug(f"Failed to extract yc token: {e}")
        return None
    
    def _extract_yses_token(self, html: str) -> Optional[str]:
        """Extract yses token from JavaScript or HTML."""
        try:
            # Look for yses token in JavaScript
            yses_pattern = r'yses["\']?\s*[:=]\s*["\']([^"\']+)["\']'
            match = re.search(yses_pattern, html, re.IGNORECASE)
            if match:
                return match.group(1)
            
            # Look for yses in cookie setting JavaScript
            cookie_pattern = r'cookies?\.set\(["\']yses["\'],\s*["\']([^"\']+)["\']'
            match = re.search(cookie_pattern, html, re.IGNORECASE)
            if match:
                return match.group(1)
                
        except Exception as e:
            logger.debug(f"Failed to extract yses token: {e}")
        return None
    
    def refresh_cookies_from_main_page(self) -> bool:
        """
        Refresh cookies by accessing the main YOPmail page.
        
        Returns:
            True if cookies were successfully refreshed
        """
        try:
            logger.info("Refreshing cookies from main page...")
            
            # Access main page
            resp = self.client.get("https://yopmail.com/")
            resp.raise_for_status()
            
            # Extract cookies from response
            detected_cookies = self.detect_cookies_from_response(resp.text)
            
            # Update cookie state
            if detected_cookies:
                self._update_cookie_state(detected_cookies)
                logger.info("Cookies refreshed successfully")
                return True
            else:
                logger.warning("No cookies detected from main page")
                return False
                
        except Exception as e:
            logger.error(f"Failed to refresh cookies: {e}")
            return False
    
    def refresh_cookies_from_wm_page(self, mailbox: str) -> bool:
        """
        Refresh cookies by accessing the webmail page.
        
        Args:
            mailbox: Mailbox name
            
        Returns:
            True if cookies were successfully refreshed
        """
        try:
            logger.info(f"Refreshing cookies from WM page for {mailbox}...")
            
            # Access WM page with login parameter
            wm_url = f"https://yopmail.com/en/wm"
            params = {"login": mailbox}
            
            resp = self.client.get(wm_url, params=params)
            resp.raise_for_status()
            
            # Extract cookies from response
            detected_cookies = self.detect_cookies_from_response(resp.text)
            
            # Update cookie state
            if detected_cookies:
                self._update_cookie_state(detected_cookies)
                logger.info("Cookies refreshed from WM page")
                return True
            else:
                logger.warning("No cookies detected from WM page")
                return False
                
        except Exception as e:
            logger.error(f"Failed to refresh cookies from WM page: {e}")
            return False
    
    def _update_cookie_state(self, detected_cookies: Dict[str, str]) -> None:
        """Update the internal cookie state."""
        current_time = time.strftime("%H:%M")
        
        # Update time cookie
        self.cookie_state.ytime = current_time
        
        # Update detected cookies
        if 'yc' in detected_cookies:
            self.cookie_state.yc = detected_cookies['yc']
            self._set_cookie("yc", detected_cookies['yc'])
        
        if 'yses' in detected_cookies:
            self.cookie_state.yses = detected_cookies['yses']
            self._set_cookie("yses", detected_cookies['yses'])
        
        if 'yp_token' in detected_cookies:
            self.cookie_state.yp_token = detected_cookies['yp_token']
        
        # Update timestamp
        self.cookie_state.last_updated = time.time()
        
        logger.debug("Cookie state updated successfully")
    
    def _set_cookie(self, name: str, value: str) -> None:
        """Set a cookie in the HTTP client."""
        try:
            self.client.cookies.set(
                name,
                value,
                domain=".yopmail.com",
                path="/"
            )
            logger.debug(f"Cookie set: {name}={value[:10]}...")
        except Exception as e:
            logger.warning(f"Failed to set cookie {name}: {e}")
    
    def ensure_fresh_cookies(self, mailbox: str) -> bool:
        """
        Ensure cookies are fresh and valid.
        
        Args:
            mailbox: Mailbox name
            
        Returns:
            True if cookies are fresh or successfully refreshed
        """
        # Check if cookies are expired
        if self.cookie_state.is_expired():
            logger.info("Cookies expired, refreshing...")
            return self.refresh_cookies_from_main_page()
        
        # Check if we have required cookies
        if not self.cookie_state.yc or not self.cookie_state.yses:
            logger.info("Missing required cookies, refreshing...")
            return self.refresh_cookies_from_main_page()
        
        # Update mailbox cookie
        self.cookie_state.ywm = mailbox
        self._set_cookie("ywm", mailbox)
        
        logger.debug("Cookies are fresh and valid")
        return True
    
    def get_yp_token(self) -> Optional[str]:
        """Get the current yp token."""
        return self.cookie_state.yp_token
    
    def get_cookie_state(self) -> CookieState:
        """Get the current cookie state."""
        return self.cookie_state
    
    def is_authenticated(self) -> bool:
        """Check if we have valid authentication."""
        return (
            self.cookie_state.yc is not None and
            self.cookie_state.yses is not None and
            self.cookie_state.yp_token is not None
        )
