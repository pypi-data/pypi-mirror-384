"""
Dynamic cookie fetcher for YOPmail client.

This module handles fetching fresh cookies by visiting Yopmail pages
and extracting authentication tokens dynamically instead of using
hardcoded cookie values.
"""

import time
import logging
import re
from typing import Dict, Optional, Tuple, Any
from bs4 import BeautifulSoup
import httpx

from .exceptions import CookieSetupError, AuthenticationError
from .constants import BASE_URL, DEFAULT_HEADERS

logger = logging.getLogger(__name__)


class DynamicCookieFetcher:
    """
    Fetches fresh cookies by visiting Yopmail pages and extracting
    authentication tokens dynamically.
    """
    
    def __init__(self, client: Optional[httpx.Client] = None, proxy_manager: Optional['ProxyManager'] = None):
        """
        Initialize the dynamic cookie fetcher.
        
        Args:
            client: Optional httpx client instance
            proxy_manager: Optional proxy manager for proxy configuration
        """
        self.proxy_manager = proxy_manager
        self.client = client or self._create_default_client()
        self.fetched_cookies: Dict[str, str] = {}
        self.last_fetch_time: float = 0
        self.cookie_validity_duration: int = 300  # 5 minutes
    
    def _create_default_client(self) -> httpx.Client:
        """Create a default HTTP client for cookie fetching."""
        client_kwargs = {
            "base_url": BASE_URL,
            "headers": DEFAULT_HEADERS,
            "follow_redirects": True,
            "timeout": 30
        }
        
        # Add proxy if available
        if self.proxy_manager and self.proxy_manager.is_proxy_enabled():
            proxy_config = self.proxy_manager.get_proxy_config()
            if proxy_config.http_proxy:
                # For httpx, proxy authentication should be in the URL
                proxy_url = proxy_config.http_proxy
                if proxy_config.auth:
                    # Add auth to proxy URL if not already present
                    if '@' not in proxy_url:
                        username, password = proxy_config.auth
                        proxy_url = f"http://{username}:{password}@{proxy_url.split('://')[1]}"
                client_kwargs["proxy"] = proxy_url
                logger.debug("DynamicCookieFetcher using proxy")
        
        return httpx.Client(**client_kwargs)
    
    def fetch_fresh_cookies(self, mailbox: str) -> Dict[str, str]:
        """
        Fetch fresh cookies by visiting Yopmail pages.
        
        Args:
            mailbox: Mailbox name to set up cookies for
            
        Returns:
            Dictionary of fresh cookies
            
        Raises:
            CookieSetupError: If cookie fetching fails
        """
        try:
            logger.info(f"Fetching fresh cookies for mailbox: {mailbox}")
            
            # Step 1: Visit main Yopmail page to establish session
            main_cookies = self._visit_main_page()
            
            # Step 2: Visit webmail page to get mailbox-specific cookies
            wm_cookies = self._visit_webmail_page(mailbox)
            
            # Step 3: Extract authentication tokens from pages
            auth_tokens = self._extract_auth_tokens(mailbox)
            
            # Combine all cookies
            fresh_cookies = {
                **main_cookies,
                **wm_cookies,
                **auth_tokens,
                "ywm": mailbox,  # Set mailbox cookie
                "ytime": time.strftime("%H:%M")  # Set current time
            }
            
            # Store fetched cookies
            self.fetched_cookies = fresh_cookies
            self.last_fetch_time = time.time()
            
            logger.info(f"Successfully fetched {len(fresh_cookies)} fresh cookies")
            return fresh_cookies
            
        except Exception as e:
            logger.error(f"Failed to fetch fresh cookies: {e}")
            raise CookieSetupError("dynamic_fetch", str(e))
    
    def _visit_main_page(self) -> Dict[str, str]:
        """
        Visit the main Yopmail page to establish session and get initial cookies.
        
        Returns:
            Dictionary of cookies from main page
        """
        try:
            logger.debug("Visiting main Yopmail page...")
            
            # Visit main page
            resp = self.client.get("/")
            resp.raise_for_status()
            
            # Extract cookies from response headers
            cookies = self._extract_cookies_from_headers(resp.headers)
            
            # Extract cookies from HTML content
            html_cookies = self._extract_cookies_from_html(resp.text)
            cookies.update(html_cookies)
            
            logger.debug(f"Extracted {len(cookies)} cookies from main page")
            return cookies
            
        except Exception as e:
            logger.warning(f"Failed to visit main page: {e}")
            return {}
    
    def _visit_webmail_page(self, mailbox: str) -> Dict[str, str]:
        """
        Visit the webmail page to get mailbox-specific cookies.
        
        Args:
            mailbox: Mailbox name
            
        Returns:
            Dictionary of cookies from webmail page
        """
        try:
            logger.debug(f"Visiting webmail page for {mailbox}...")
            
            # Visit webmail page with login parameter
            wm_url = "/en/wm"
            params = {"login": mailbox}
            
            resp = self.client.get(wm_url, params=params)
            resp.raise_for_status()
            
            # Extract cookies from response headers
            cookies = self._extract_cookies_from_headers(resp.headers)
            
            # Extract cookies from HTML content
            html_cookies = self._extract_cookies_from_html(resp.text)
            cookies.update(html_cookies)
            
            logger.debug(f"Extracted {len(cookies)} cookies from webmail page")
            return cookies
            
        except Exception as e:
            logger.warning(f"Failed to visit webmail page: {e}")
            return {}
    
    def _extract_auth_tokens(self, mailbox: str) -> Dict[str, str]:
        """
        Extract authentication tokens from Yopmail pages.
        
        Args:
            mailbox: Mailbox name
            
        Returns:
            Dictionary of authentication tokens
        """
        try:
            logger.debug("Extracting authentication tokens...")
            
            # Visit the inbox page to get authentication tokens
            inbox_url = "/inbox"
            params = {
                "login": mailbox,
                "p": "1",
                "d": "",
                "ctrl": "",
                "yp": "ZAGplZmp0ZmR3ZQN4ZGx1ZGR"  # Default token for initial request
            }
            
            resp = self.client.get(inbox_url, params=params)
            resp.raise_for_status()
            
            # Extract tokens from HTML
            tokens = self._extract_tokens_from_html(resp.text)
            
            logger.debug(f"Extracted {len(tokens)} authentication tokens")
            return tokens
            
        except Exception as e:
            logger.warning(f"Failed to extract auth tokens: {e}")
            return {}
    
    def _extract_cookies_from_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Extract cookies from HTTP response headers."""
        cookies = {}
        
        try:
            # Get Set-Cookie headers
            set_cookie_headers = headers.get_list("set-cookie") if hasattr(headers, 'get_list') else []
            if not set_cookie_headers:
                # Fallback for different header formats
                set_cookie_headers = [v for k, v in headers.items() if k.lower() == 'set-cookie']
            
            for cookie_header in set_cookie_headers:
                # Parse cookie header: "name=value; domain=.yopmail.com; path=/"
                cookie_parts = cookie_header.split(';')[0].strip()
                if '=' in cookie_parts:
                    name, value = cookie_parts.split('=', 1)
                    cookies[name.strip()] = value.strip()
                    
        except Exception as e:
            logger.debug(f"Failed to extract cookies from headers: {e}")
        
        return cookies
    
    def _extract_cookies_from_html(self, html: str) -> Dict[str, str]:
        """Extract cookies from HTML content (JavaScript cookie setting)."""
        cookies = {}
        
        try:
            # Look for JavaScript cookie setting patterns
            patterns = [
                r'cookies?\.set\(["\']([^"\']+)["\'],\s*["\']([^"\']+)["\']',
                r'document\.cookie\s*=\s*["\']([^=]+)=([^;]+)',
                r'cookie\s*=\s*["\']([^=]+)=([^;]+)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for name, value in matches:
                    cookies[name.strip()] = value.strip()
                    
        except Exception as e:
            logger.debug(f"Failed to extract cookies from HTML: {e}")
        
        return cookies
    
    def _extract_tokens_from_html(self, html: str) -> Dict[str, str]:
        """Extract authentication tokens from HTML content."""
        tokens = {}
        
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # Extract yp token from input field
            yp_input = soup.find("input", {"id": "yp"})
            if yp_input and yp_input.get("value"):
                tokens["yp_token"] = yp_input["value"]
                logger.debug(f"Found yp token: {yp_input['value'][:10]}...")
            
            # Look for other tokens in JavaScript
            js_patterns = {
                "yc": r'yc["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                "yses": r'yses["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                "compte": r'compte["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            }
            
            for token_name, pattern in js_patterns.items():
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    tokens[token_name] = match.group(1)
                    logger.debug(f"Found {token_name} token: {match.group(1)[:10]}...")
                    
        except Exception as e:
            logger.debug(f"Failed to extract tokens from HTML: {e}")
        
        return tokens
    
    def get_fresh_cookies(self, mailbox: str, force_refresh: bool = False) -> Dict[str, str]:
        """
        Get fresh cookies, fetching them if necessary.
        
        Args:
            mailbox: Mailbox name
            force_refresh: Force refresh even if cookies are still valid
            
        Returns:
            Dictionary of fresh cookies
        """
        # Check if we need to refresh cookies
        if (force_refresh or 
            not self.fetched_cookies or 
            self._are_cookies_expired()):
            
            logger.info("Fetching fresh cookies...")
            return self.fetch_fresh_cookies(mailbox)
        
        # Return cached cookies if still valid
        logger.debug("Using cached cookies")
        return self.fetched_cookies.copy()
    
    def _are_cookies_expired(self) -> bool:
        """Check if fetched cookies are expired."""
        if not self.last_fetch_time:
            return True
        
        return time.time() - self.last_fetch_time > self.cookie_validity_duration
    
    def set_cookies_in_client(self, client: httpx.Client, cookies: Dict[str, str]) -> None:
        """
        Set cookies in an HTTP client.
        
        Args:
            client: HTTP client to set cookies in
            cookies: Dictionary of cookies to set
        """
        try:
            for name, value in cookies.items():
                client.cookies.set(
                    name,
                    value,
                    domain=".yopmail.com",
                    path="/"
                )
            logger.debug(f"Set {len(cookies)} cookies in client")
            
        except Exception as e:
            logger.warning(f"Failed to set cookies in client: {e}")
    
    def validate_cookies(self, cookies: Dict[str, str]) -> bool:
        """
        Validate that required cookies are present.
        
        Args:
            cookies: Dictionary of cookies to validate
            
        Returns:
            True if cookies are valid, False otherwise
        """
        required_cookies = ["ytime", "ywm"]
        optional_cookies = ["yc", "yses", "yp_token", "compte"]
        
        # Check required cookies
        for cookie_name in required_cookies:
            if cookie_name not in cookies or not cookies[cookie_name]:
                logger.warning(f"Missing required cookie: {cookie_name}")
                return False
        
        # Check if we have at least some optional cookies
        optional_count = sum(1 for cookie_name in optional_cookies 
                           if cookie_name in cookies and cookies[cookie_name])
        
        if optional_count == 0:
            logger.warning("No optional authentication cookies found")
            return False
        
        logger.debug(f"Cookie validation passed ({optional_count} optional cookies found)")
        return True
    
    def close(self) -> None:
        """Close the HTTP client and clean up resources."""
        if hasattr(self, 'client') and self.client:
            self.client.close()
        logger.debug("Dynamic cookie fetcher closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
