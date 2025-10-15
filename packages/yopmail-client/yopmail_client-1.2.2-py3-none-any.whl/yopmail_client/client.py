"""
Main YOPmail client implementation.

This module contains the core YOPMailClient class that provides
a clean API for interacting with YOPmail services.
"""

import logging
import time
from typing import List, Optional, Dict, Any
import httpx
from bs4 import BeautifulSoup

from .exceptions import (
    YOPMailError, 
    HTTPError, 
    MissingTokenError, 
    AuthenticationError,
    NetworkError
)
from .utils import HTMLParser, RequestBuilder, Message, validate_mailbox_name, sanitize_mailbox_name
from .cookies import CookieManager
from .cookie_detector import CookieDetector
from .rate_limiter import RateLimiter
from .proxy_manager import ProxyManager
from .constants import (
    BASE_URL, 
    DEFAULT_HEADERS, 
    LOGIN_HEADERS, 
    INBOX_HEADERS, 
    SEND_HEADERS,
    ENDPOINTS,
    DEFAULT_CONFIG
)

logger = logging.getLogger(__name__)


class YOPMailClient:
    """
    A clean, modular client for YOPmail disposable email service.
    
    This client provides methods to interact with YOPmail services including
    inbox access, message retrieval, and basic email operations.
    
    Example:
        >>> client = YOPMailClient("testuser")
        >>> client.open_inbox()
        >>> messages = client.list_messages()
        >>> for msg in messages:
        ...     print(f"Subject: {msg.subject}")
    """
    
    def __init__(
        self, 
        mailbox: str, 
        config: Optional[Dict[str, Any]] = None,
        client: Optional[httpx.Client] = None,
        use_dynamic_cookies: bool = True
    ):
        """
        Initialize YOPmail client.
        
        Args:
            mailbox: Mailbox name (without @yopmail.com)
            config: Optional configuration dictionary
            client: Optional httpx client instance
            use_dynamic_cookies: Whether to use dynamic cookie fetching (default: True)
        """
        self.mailbox = sanitize_mailbox_name(mailbox)
        self.config = self._merge_config(config or {})
        self.yp_token: Optional[str] = None
        self.use_dynamic_cookies = use_dynamic_cookies
        
        # Initialize managers first
        self.rate_limiter = RateLimiter(self.config)
        self.proxy_manager = ProxyManager(self.config)
        
        # Initialize HTTP client (after managers are ready)
        self.client = client or self._create_http_client()
        self.cookie_manager = CookieManager(self.client, use_dynamic_cookies=use_dynamic_cookies, proxy_manager=self.proxy_manager)
        self.cookie_detector = CookieDetector(self.client)
        
        # Initialize dynamic cookies if enabled
        if use_dynamic_cookies:
            self._initialize_dynamic_cookies()
        
        logger.info(f"YOPmail client initialized for mailbox: {self.mailbox}")
    
    def _merge_config(self, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge user configuration with defaults."""
        config = DEFAULT_CONFIG.__dict__.copy()
        config.update(user_config)
        return config
    
    def _create_http_client(self) -> httpx.Client:
        """Create configured HTTP client with proxy support."""
        client_kwargs = {
            "base_url": self.config.get("base_url", BASE_URL),
            "headers": DEFAULT_HEADERS,
            "follow_redirects": self.config.get("follow_redirects", True),
            "timeout": self.config.get("timeout", 30)
        }
        
        # Add proxy configuration if enabled
        if self.proxy_manager.is_proxy_enabled():
            proxies = self.proxy_manager.get_httpx_proxies()
            if proxies:
                client_kwargs["proxies"] = proxies
                logger.info(f"Using proxy: {self.proxy_manager.get_proxy_info()}")
        
        return httpx.Client(**client_kwargs)
    
    def _initialize_dynamic_cookies(self) -> None:
        """Initialize dynamic cookies by fetching them from Yopmail pages."""
        try:
            logger.info("Initializing dynamic cookies...")
            
            # Set up initial cookies using dynamic fetching
            self.cookie_manager.set_mailbox_cookie(self.mailbox)
            
            # Extract yp token from fresh cookies if available
            fresh_cookies = self.cookie_manager.get_dynamic_cookies(self.mailbox)
            if 'yp_token' in fresh_cookies:
                self.yp_token = fresh_cookies['yp_token']
                logger.info(f"Extracted yp token from dynamic cookies: {self.yp_token[:10]}...")
            
            logger.info("Dynamic cookies initialized successfully")
            
        except Exception as e:
            logger.warning(f"Failed to initialize dynamic cookies: {e}")
            # Fallback to static cookies
            logger.info("Falling back to static cookie setup")
            self.cookie_manager.use_dynamic_cookies = False
            self.cookie_manager._setup_default_cookies()
    
    def open_inbox(self) -> None:
        """
        Initialize inbox access and extract authentication token.
        
        This method must be called before accessing messages.
        
        Raises:
            HTTPError: If the request fails
            MissingTokenError: If authentication token cannot be extracted
        """
        try:
            # Check rate limiting before making request
            delay = self.rate_limiter.get_request_delay()
            if delay > 0:
                logger.debug(f"Rate limiting delay: {delay:.1f}s")
                time.sleep(delay)
            
            # Ensure we have fresh cookies
            if self.use_dynamic_cookies:
                # Use dynamic cookie refresh
                if not self.cookie_manager.refresh_cookies(self.mailbox):
                    logger.warning("Failed to refresh dynamic cookies, using fallback method")
                    # Fallback to basic cookie setup
                    self.cookie_manager.set_mailbox_cookie(self.mailbox)
            else:
                # Use existing cookie detector
                if not self.cookie_detector.ensure_fresh_cookies(self.mailbox):
                    logger.warning("Failed to refresh cookies, using fallback method")
                    # Fallback to basic cookie setup
                    self.cookie_manager.set_mailbox_cookie(self.mailbox)
            
            # Access main page to establish session
            logger.debug("Accessing main page to establish session")
            main_resp = self.client.get(ENDPOINTS["main"])
            
            # Check for rate limiting
            if self._handle_rate_limit_response(main_resp):
                return self.open_inbox()  # Retry after rate limiting
            
            main_resp.raise_for_status()
            
            # Try to extract yp token from the response
            detected_cookies = self.cookie_detector.detect_cookies_from_response(main_resp.text)
            if 'yp_token' in detected_cookies:
                self.yp_token = detected_cookies['yp_token']
                logger.info(f"Extracted yp token from main page: {self.yp_token[:10]}...")
            else:
                # Fallback to known working token
                self.yp_token = "ZAGplZmp0ZmR3ZQN4ZGx1ZGR"
                logger.warning("Using fallback yp token")
            
            logger.info(f"Inbox opened successfully for {self.mailbox}")
            
        except httpx.HTTPStatusError as e:
            raise HTTPError(e.response.status_code, str(e.request.url), e.response.text)
        except httpx.RequestError as e:
            raise NetworkError("inbox initialization", str(e))
        except Exception as e:
            logger.error(f"Failed to open inbox: {e}")
            raise YOPMailError(f"Failed to open inbox: {e}")
    
    def list_messages(self, page: int = 1) -> List[Message]:
        """
        Retrieve list of messages from inbox.
        
        Args:
            page: Page number to retrieve (default: 1)
            
        Returns:
            List of Message objects
            
        Raises:
            HTTPError: If the request fails
            ParseError: If message parsing fails
        """
        if self.yp_token is None:
            self.open_inbox()
        
        try:
            # Build request parameters
            params = RequestBuilder.build_inbox_params(
                self.mailbox, 
                self.yp_token, 
                page
            )
            
            # Make request with proper headers
            headers = {**DEFAULT_HEADERS, **INBOX_HEADERS}
            resp = self.client.get(ENDPOINTS["inbox"], params=params, headers=headers)
            resp.raise_for_status()
            
            # Check if we got a valid response (not "Loading..." page)
            if self._is_loading_page(resp.text):
                logger.warning("Received loading page, cookies may be expired")
                # Try to refresh cookies and retry
                if self._refresh_and_retry():
                    return self.list_messages(page)
                else:
                    raise AuthenticationError("Failed to refresh authentication")
            
            # Parse messages from response
            messages = HTMLParser.parse_messages(resp.text)
            
            logger.info(f"Retrieved {len(messages)} messages from page {page}")
            return messages
            
        except httpx.HTTPStatusError as e:
            # Check if it's an authentication error
            if e.response.status_code == 400:
                logger.warning("Authentication error, attempting to refresh cookies")
                if self._refresh_and_retry():
                    return self.list_messages(page)
            raise HTTPError(e.response.status_code, str(e.request.url), e.response.text)
        except httpx.RequestError as e:
            raise NetworkError("message listing", str(e))
        except Exception as e:
            logger.error(f"Failed to list messages: {e}")
            raise YOPMailError(f"Failed to list messages: {e}")
    
    def fetch_message(self, message_id: str) -> str:
        """
        Fetch email message content (body only, not full HTML page).
        
        Args:
            message_id: ID of the message to fetch
            
        Returns:
            Email message body content (text only)
            
        Raises:
            HTTPError: If the request fails
        """
        try:
            # Use requests library for message fetching (httpx doesn't work with YOPmail)
            import requests
            import time
            from bs4 import BeautifulSoup
            
            # Create session with cookies
            session = requests.Session()
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            })
            
            # Add proxy configuration if enabled
            if self.proxy_manager.is_proxy_enabled():
                proxies = self.proxy_manager.get_requests_proxies()
                if proxies:
                    session.proxies.update(proxies)
                    logger.debug(f"Using proxy for fetch_message: {proxies}")
                
                # Add proxy auth if available
                proxy_auth = self.proxy_manager.get_proxy_auth()
                if proxy_auth:
                    session.auth = proxy_auth
            
            # Set cookies like browser
            current_time = time.strftime("%H:%M")
            session.cookies.set("ytime", current_time, domain=".yopmail.com", path="/")
            session.cookies.set("ywm", self.mailbox, domain=".yopmail.com", path="/")
            session.cookies.set("yc", "EAGNlBGD2Awx4ZmpkZGN4ZQV", domain=".yopmail.com", path="/")
            session.cookies.set("yses", "zz6dtenHstru+L/GLPPQD4a5iJbTzoLzBsyP3HkfhNIwBQRWRdGPgRYto8uoBVoi", domain=".yopmail.com", path="/")
            
            # Access pages to establish session
            session.get("https://yopmail.com/")
            session.get("https://yopmail.com/en/wm")
            
            # Format message ID properly
            from .utils import format_message_id
            formatted_id = format_message_id(message_id)
            
            # Build the exact URL like the working test
            mail_url = f"https://yopmail.com/mail?b={self.mailbox}&id={formatted_id}"
            
            # Add proper headers for mail request (like browser)
            mail_headers = {
                "Referer": "https://yopmail.com/wm",
                "Sec-Fetch-Dest": "iframe",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
            }
            
            # Make request with proper headers
            resp = session.get(mail_url, headers=mail_headers)
            resp.raise_for_status()
            
            # Parse HTML and extract only the email body content
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Try to find the email body in different possible containers
            email_body = None
            
            # First, look for iframe content (YOPmail often loads email in iframe)
            iframes = soup.find_all('iframe')
            if iframes:
                # If there's an iframe, the email content might be in its src
                for iframe in iframes:
                    src = iframe.get('src', '')
                    if 'mail' in src.lower() or 'message' in src.lower():
                        # This might be the email content iframe
                        logger.debug(f"Found potential email iframe: {src}")
            
            # Look for email content in various containers
            body_selectors = [
                '#mailctn #mail',  # YOPmail specific email body container
                '#mailctn',  # YOPmail email container
                '#mail',  # Direct mail container
                'div[style*="font-family"]',  # YOPmail often uses inline styles
                'div[style*="padding"]',  # Email content usually has padding
                'div[class*="mail"]',
                'div[class*="message"]', 
                'div[class*="content"]',
                'div[class*="body"]',
                '.mail-body',
                '#mail-body',
                'div[style*="background"]',  # Email content areas
            ]
            
            for selector in body_selectors:
                body_element = soup.select_one(selector)
                if body_element:
                    text = body_element.get_text(strip=True)
                    # Look for content that seems like email body (not headers)
                    # For YOPmail, we want to accept shorter content if it's from the mail container
                    if (len(text) > 5 and 
                        not any(header in text.lower() for header in ['subject:', 'from:', 'date:', 'to:']) and
                        not any(ui in text.lower() for ui in ['deliverability', 'reply', 'forward', 'print', 'delete', 'html', 'text', 'headers', 'source', 'download'])):
                        email_body = body_element
                        logger.debug(f"Found email body with selector: {selector} -> {text}")
                        break
            
            # If no specific body found, look for the actual email content
            if not email_body:
                all_divs = soup.find_all('div')
                best_div = None
                best_score = 0
                
                for div in all_divs:
                    text = div.get_text(strip=True)
                    # Look for content that appears to be email body (not headers)
                    if len(text) > 5 and len(text) < 1000:  # Reasonable email body length
                        score = 0
                        
                        # Bonus for content that looks like email body
                        email_body_indicators = [
                            'hello', 'dear', 'thanks', 'regards', 'sincerely', 'best',
                            'hi', 'hey', 'greetings', 'yours', 'kind regards',
                            'please', 'thank you', 'welcome', 'congratulations'
                        ]
                        
                        for indicator in email_body_indicators:
                            if indicator in text.lower():
                                score += 10
                        
                        # Penalize if it contains header-like content
                        header_indicators = ['subject:', 'from:', 'date:', 'to:', 'sent:', 'received:']
                        for header in header_indicators:
                            if header in text.lower():
                                score -= 20
                        
                        # Bonus for content that doesn't look like navigation/UI
                        ui_indicators = ['deliverability', 'reply', 'forward', 'print', 'delete', 'html', 'text', 'headers', 'source', 'download']
                        ui_penalty = 0
                        for ui in ui_indicators:
                            if ui in text.lower():
                                ui_penalty += 5
                        score -= ui_penalty
                        
                        # Base score on length (but not too long)
                        score += min(len(text), 100)
                        
                        if score > best_score and score > 0:
                            best_score = score
                            best_div = div
                            logger.debug(f"Found potential email body with score {score}: {text[:50]}...")
                
                if best_div:
                    email_body = best_div
            
            # Extract text content
            if email_body:
                message_content = email_body.get_text(strip=True)
                # Clean up the content
                message_content = message_content.replace('\n', ' ').replace('\r', ' ')
                # Remove multiple spaces
                import re
                message_content = re.sub(r'\s+', ' ', message_content).strip()
                
                logger.info(f"Extracted message content for ID: {message_id} ({len(message_content)} chars)")
                return message_content
            else:
                # Fallback: return the full page text if we can't find specific body
                logger.warning("Could not find email body, returning full page text")
                full_text = soup.get_text(strip=True)
                return re.sub(r'\s+', ' ', full_text).strip()
            
        except Exception as e:
            logger.error(f"Failed to fetch message: {e}")
            raise YOPMailError(f"Failed to fetch message: {e}")
    
    def send_message(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """
        Send an email message to a YOPmail address.
        
        Note: YOPmail only allows sending emails to other YOPmail addresses.
        
        Args:
            to: Recipient email address (must be @yopmail.com)
            subject: Email subject
            body: Email body
            
        Returns:
            Dictionary with send result information
            
        Raises:
            ValueError: If recipient is not a YOPmail address
            HTTPError: If the request fails
            YOPMailError: If sending fails
        """
        # Validate recipient is a YOPmail address
        if not to.endswith('@yopmail.com'):
            raise ValueError("YOPmail only allows sending emails to @yopmail.com addresses")
        
        # Ensure we have authentication
        if self.yp_token is None:
            self.open_inbox()
        
        try:
            # Check rate limiting before making request
            delay = self.rate_limiter.get_request_delay()
            if delay > 0:
                logger.debug(f"Rate limiting delay: {delay:.1f}s")
                time.sleep(delay)
            
            # Prepare form data
            form_data = {
                'msgfrom': f"{self.mailbox}@yopmail.com",
                'msgto': to,
                'msgsubject': subject,
                'msgbody': body
            }
            
            # Make request with proper headers
            headers = {**DEFAULT_HEADERS, **SEND_HEADERS}
            resp = self.client.post(
                ENDPOINTS["send"], 
                data=form_data, 
                headers=headers
            )
            
            # Check for rate limiting
            if self._handle_rate_limit_response(resp):
                return self.send_message(to, subject, body)  # Retry after rate limiting
            
            resp.raise_for_status()
            
            # Parse response
            response_text = resp.text.strip()
            
            # Check for error messages
            if "You can only send email to YOPmail addresses" in response_text:
                raise ValueError("YOPmail only allows sending emails to @yopmail.com addresses")
            
            # Check for success indicators
            success_indicators = [
                "msgto|",  # Success response format
                "sent successfully",
                "message sent",
                "your message has been sent",
                "ok|"
            ]
            
            is_success = any(indicator in response_text.lower() for indicator in success_indicators)
            
            if is_success:
                logger.info(f"Message sent successfully to {to}")
                return {
                    "success": True,
                    "recipient": to,
                    "subject": subject,
                    "message": "Message sent successfully"
                }
            else:
                # Check for specific error messages
                error_messages = [
                    "invalid recipient",
                    "recipient not found",
                    "delivery failed",
                    "message rejected"
                ]
                
                for error_msg in error_messages:
                    if error_msg in response_text.lower():
                        raise YOPMailError(f"Send failed: {error_msg}")
                
                # Generic error
                raise YOPMailError(f"Send failed: {response_text}")
            
        except httpx.HTTPStatusError as e:
            raise HTTPError(e.response.status_code, str(e.request.url), e.response.text)
        except httpx.RequestError as e:
            raise NetworkError("message sending", str(e))
        except (ValueError, YOPMailError):
            raise  # Re-raise validation and YOPmail errors
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise YOPMailError(f"Failed to send message: {e}")
    
    def get_inbox_info(self) -> Dict[str, Any]:
        """
        Get basic information about the inbox.
        
        Returns:
            Dictionary with inbox information
        """
        messages = self.list_messages()
        return {
            "mailbox": self.mailbox,
            "message_count": len(messages),
            "has_messages": len(messages) > 0,
            "messages": [
                {
                    "id": msg.id,
                    "subject": msg.subject,
                    "sender": msg.sender,
                    "time": msg.time
                }
                for msg in messages
            ]
        }
    
    def close(self) -> None:
        """Close the HTTP client and clean up resources."""
        if hasattr(self, 'client'):
            self.client.close()
        if hasattr(self, 'cookie_manager'):
            self.cookie_manager.close()
        logger.info("YOPmail client closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def _is_loading_page(self, html: str) -> bool:
        """Check if the response is a loading page indicating expired cookies."""
        loading_indicators = [
            "Loading ...",
            "w.rwm()",
            "reload webmail",
            "javascript:void(0)"
        ]
        
        html_lower = html.lower()
        return any(indicator.lower() in html_lower for indicator in loading_indicators)
    
    def _refresh_and_retry(self) -> bool:
        """Refresh cookies and authentication tokens."""
        try:
            logger.info("Attempting to refresh authentication...")
            
            # Try to refresh cookies from main page
            if self.cookie_detector.refresh_cookies_from_main_page():
                # Update yp token
                new_yp_token = self.cookie_detector.get_yp_token()
                if new_yp_token:
                    self.yp_token = new_yp_token
                    logger.info("Authentication refreshed successfully")
                    return True
            
            # Try WM page as fallback
            if self.cookie_detector.refresh_cookies_from_wm_page(self.mailbox):
                new_yp_token = self.cookie_detector.get_yp_token()
                if new_yp_token:
                    self.yp_token = new_yp_token
                    logger.info("Authentication refreshed from WM page")
                    return True
            
            logger.error("Failed to refresh authentication")
            return False
            
        except Exception as e:
            logger.error(f"Error during authentication refresh: {e}")
            return False
    
    def _handle_rate_limit_response(self, response: httpx.Response) -> bool:
        """
        Handle rate limiting response and return True if retry is needed.
        
        Args:
            response: HTTP response to check
            
        Returns:
            True if rate limited and retry is needed, False otherwise
        """
        try:
            should_retry, delay = self.rate_limiter.handle_rate_limit(
                response.status_code,
                dict(response.headers),
                response.text
            )
            
            if should_retry:
                logger.warning(f"Rate limited, waiting {delay:.1f} seconds...")
                time.sleep(delay)
                self.rate_limiter.record_request()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error handling rate limit: {e}")
            return False
    
    def get_rss_feed_url(self, mailbox: Optional[str] = None) -> str:
        """
        Get RSS feed URL for a YOPmail address.
        
        Args:
            mailbox: Mailbox name (without @yopmail.com). If None, uses current client mailbox.
            
        Returns:
            RSS feed URL for the specified mailbox
        """
        target_mailbox = mailbox or self.mailbox
        # RSS feed URL format: https://yopmail.com/rss?login=mailbox&h=hash
        # For now, return the basic URL without hash (hash is generated by YOPmail)
        return f"https://yopmail.com/rss?login={target_mailbox}"
    
    def get_rss_feed_data(self, mailbox: Optional[str] = None) -> Dict[str, Any]:
        """
        Get RSS feed data for a YOPmail address.
        
        Args:
            mailbox: Mailbox name (without @yopmail.com). If None, uses current client mailbox.
            
        Returns:
            Dictionary with RSS feed information and messages
            
        Raises:
            HTTPError: If the request fails
            YOPMailError: If RSS feed cannot be retrieved
        """
        target_mailbox = mailbox or self.mailbox
        
        try:
            # Use fresh cookies to potentially avoid rate limits
            self._set_fresh_cookies()
            
            # Check rate limiting before making request
            delay = self.rate_limiter.get_request_delay()
            if delay > 0:
                logger.debug(f"Rate limiting delay: {delay:.1f}s")
                time.sleep(delay)
            
            # First, get the RSS feed page to extract the proper RSS URL with hash
            gen_rss_url = f"https://yopmail.com/gen-rss?login={target_mailbox}"
            headers = {**DEFAULT_HEADERS}
            resp = self.client.get(gen_rss_url, headers=headers)
            
            # Check for rate limiting
            if self._handle_rate_limit_response(resp):
                return self.get_rss_feed_data(mailbox)  # Retry after rate limiting
            
            resp.raise_for_status()
            
            # Parse the RSS page to extract the actual RSS URL with hash
            rss_url = self._extract_rss_url_from_page(resp.text, target_mailbox)
            
            # Now get the actual RSS feed data
            rss_resp = self.client.get(rss_url, headers=headers)
            rss_resp.raise_for_status()
            
            # Parse RSS content
            rss_content = rss_resp.text
            
            # Extract messages from RSS content
            messages = self._parse_rss_content(rss_content)
            
            logger.info(f"Retrieved RSS feed for {target_mailbox} with {len(messages)} messages")
            
            return {
                "mailbox": target_mailbox,
                "rss_url": rss_url,
                "message_count": len(messages),
                "messages": messages,
                "raw_content": rss_content
            }
            
        except httpx.HTTPStatusError as e:
            raise HTTPError(e.response.status_code, str(e.request.url), e.response.text)
        except httpx.RequestError as e:
            raise NetworkError("RSS feed retrieval", str(e))
        except Exception as e:
            logger.error(f"Failed to get RSS feed: {e}")
            raise YOPMailError(f"Failed to get RSS feed: {e}")
    
    def _set_fresh_cookies(self):
        """Set fresh cookies from real browser session to avoid rate limits."""
        try:
            from .constants import DEFAULT_COOKIES
            
            # Set fresh cookies to potentially avoid rate limits
            for name, value in DEFAULT_COOKIES.items():
                self.client.cookies.set(name, value, domain='.yopmail.com', path='/')
            
            logger.debug("Fresh cookies set from real browser session")
            
        except Exception as e:
            logger.warning(f"Failed to set fresh cookies: {e}")
    
    def _extract_rss_url_from_page(self, page_content: str, mailbox: str) -> str:
        """
        Extract the actual RSS URL with hash from the RSS generation page.
        
        Args:
            page_content: HTML content of the RSS generation page
            mailbox: Mailbox name
            
        Returns:
            Complete RSS URL with hash
        """
        import re
        
        # Look for the RSS URL pattern in the page content
        # Pattern: href="/rss?login=mailbox&h=hash"
        pattern = r'href="(/rss\?login=' + re.escape(mailbox) + r'&h=[^"]+)"'
        match = re.search(pattern, page_content)
        
        if match:
            rss_path = match.group(1)
            return f"https://yopmail.com{rss_path}"
        else:
            # Fallback to basic RSS URL
            return f"https://yopmail.com/rss?login={mailbox}"
    
    def _parse_rss_content(self, rss_content: str) -> List[Dict[str, Any]]:
        """
        Parse RSS content to extract message information.
        
        Args:
            rss_content: Raw RSS content (XML format)
            
        Returns:
            List of message dictionaries
        """
        messages = []
        
        try:
            # Parse XML RSS content
            from bs4 import BeautifulSoup
            
            # Suppress XML parsing warnings
            import warnings
            from bs4 import XMLParsedAsHTMLWarning
            warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
            
            soup = BeautifulSoup(rss_content, 'html.parser')
            
            # Find all item elements
            items = soup.find_all('item')
            
            for item in items:
                # Extract subject from title
                title_elem = item.find('title')
                subject = title_elem.get_text(strip=True) if title_elem else "No Subject"
                
                # Extract link
                link_elem = item.find('link')
                url = link_elem.get_text(strip=True) if link_elem else ""
                
                # Extract date
                pub_date_elem = item.find('pubdate')
                date = pub_date_elem.get_text(strip=True) if pub_date_elem else "Unknown Date"
                
                # Extract description for sender info
                desc_elem = item.find('description')
                sender = "Unknown"
                if desc_elem:
                    desc_text = desc_elem.get_text(strip=True)
                    # Look for email pattern in description
                    import re
                    email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', desc_text)
                    if email_match:
                        sender = email_match.group(1)
                
                messages.append({
                    "subject": subject,
                    "sender": sender,
                    "date": date,
                    "url": url,
                    "description": desc_elem.get_text(strip=True) if desc_elem else ""
                })
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to parse RSS content: {e}")
            # Fallback to simple text parsing
            return self._parse_rss_content_fallback(rss_content)
    
    def _parse_rss_content_fallback(self, rss_content: str) -> List[Dict[str, Any]]:
        """
        Fallback RSS content parsing for simple text format.
        
        Args:
            rss_content: Raw RSS content
            
        Returns:
            List of message dictionaries
        """
        messages = []
        
        try:
            # Split content by lines and parse each message
            lines = rss_content.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('<?xml') or line.startswith('<'):
                    continue
                
                # Parse message format: "subject sender date url"
                parts = line.split(' ')
                if len(parts) >= 4:
                    subject = parts[0]
                    sender = parts[1]
                    date = parts[2]
                    url = ' '.join(parts[3:])  # URL might contain spaces
                    
                    messages.append({
                        "subject": subject,
                        "sender": sender,
                        "date": date,
                        "url": url
                    })
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to parse RSS content (fallback): {e}")
            return []
    
    def get_proxy_info(self) -> Dict[str, Any]:
        """Get information about current proxy configuration."""
        return self.proxy_manager.get_proxy_info()
    
    def test_proxy_connection(self) -> bool:
        """Test proxy connection if enabled."""
        return self.proxy_manager.test_proxy_connection()
    
    def __repr__(self) -> str:
        """String representation of the client."""
        return f"YOPMailClient(mailbox='{self.mailbox}')"
