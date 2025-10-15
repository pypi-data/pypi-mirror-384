"""
Proxy management for YOPmail client.

This module handles proxy configuration from environment variables,
config files, and user settings with support for HTTP/HTTPS proxies.
"""

import os
import logging
from typing import Optional, Dict, Any, Union
from urllib.parse import urlparse
from dataclasses import dataclass

from .exceptions import YOPMailError
from .constants import PROXY_ENV_VARS, PROXY_CONFIG_KEYS

logger = logging.getLogger(__name__)


@dataclass
class ProxyConfig:
    """Proxy configuration."""
    enabled: bool = False
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None
    auth: Optional[tuple] = None  # (username, password)
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format for httpx."""
        proxies = {}
        if self.http_proxy:
            proxies["http://"] = self.http_proxy
        if self.https_proxy:
            proxies["https://"] = self.https_proxy
        return proxies


class ProxyManager:
    """Manages proxy configuration and setup."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize proxy manager with configuration."""
        self.config = config
        self.proxy_config = self._load_proxy_config()
        
    def _load_proxy_config(self) -> ProxyConfig:
        """Load proxy configuration from various sources."""
        proxy_config = ProxyConfig()
        
        # Check if proxy is explicitly disabled
        if self.config.get("proxy_enabled") is False:
            logger.debug("Proxy explicitly disabled in config")
            return proxy_config
        
        # Try to get proxy from config
        proxy_url = self._get_proxy_from_config()
        if proxy_url:
            proxy_config = self._parse_proxy_url(proxy_url)
            proxy_config.enabled = True
            logger.info(f"Using proxy from config: {proxy_url}")
            return proxy_config
        
        # Try to get proxy from environment variables
        env_proxy = self._get_proxy_from_env()
        if env_proxy:
            proxy_config = self._parse_proxy_url(env_proxy)
            proxy_config.enabled = True
            logger.info(f"Using proxy from environment: {env_proxy}")
            return proxy_config
        
        logger.debug("No proxy configuration found")
        return proxy_config
    
    def _get_proxy_from_config(self) -> Optional[str]:
        """Get proxy URL from configuration."""
        # Check various config keys
        for key in PROXY_CONFIG_KEYS:
            if key in self.config and self.config[key]:
                return self.config[key]
        
        # Check for proxy_enabled flag
        if self.config.get("proxy_enabled") and self.config.get("proxy_url"):
            return self.config["proxy_url"]
        
        return None
    
    def _get_proxy_from_env(self) -> Optional[str]:
        """Get proxy URL from environment variables."""
        for env_var in PROXY_ENV_VARS:
            proxy_url = os.getenv(env_var)
            if proxy_url:
                logger.debug(f"Found proxy in {env_var}: {proxy_url}")
                return proxy_url
        
        return None
    
    def _parse_proxy_url(self, proxy_url: str) -> ProxyConfig:
        """Parse proxy URL and extract configuration."""
        try:
            parsed = urlparse(proxy_url)
            
            # Build proxy URL with authentication if present
            if parsed.username and parsed.password:
                auth = (parsed.username, parsed.password)
                # Remove auth from URL
                netloc = f"{parsed.hostname}:{parsed.port}" if parsed.port else parsed.hostname
                clean_url = f"{parsed.scheme}://{netloc}"
            else:
                auth = None
                clean_url = proxy_url
            
            proxy_config = ProxyConfig(
                enabled=True,
                auth=auth
            )
            
            # Set both HTTP and HTTPS to the same proxy
            proxy_config.http_proxy = clean_url
            proxy_config.https_proxy = clean_url
            
            return proxy_config
            
        except Exception as e:
            logger.error(f"Failed to parse proxy URL '{proxy_url}': {e}")
            raise YOPMailError(f"Invalid proxy URL: {proxy_url}")
    
    def get_proxy_config(self) -> ProxyConfig:
        """Get current proxy configuration."""
        return self.proxy_config
    
    def is_proxy_enabled(self) -> bool:
        """Check if proxy is enabled."""
        return self.proxy_config.enabled
    
    def get_httpx_proxies(self) -> Dict[str, str]:
        """Get proxy configuration for httpx client."""
        if not self.proxy_config.enabled:
            return {}
        
        return self.proxy_config.to_dict()
    
    def get_requests_proxies(self) -> Dict[str, str]:
        """Get proxy configuration for requests library."""
        if not self.proxy_config.enabled:
            return {}
        
        proxies = {}
        if self.proxy_config.http_proxy:
            proxies["http"] = self.proxy_config.http_proxy
        if self.proxy_config.https_proxy:
            proxies["https"] = self.proxy_config.https_proxy
        
        return proxies
    
    def get_proxy_auth(self) -> Optional[tuple]:
        """Get proxy authentication credentials."""
        return self.proxy_config.auth
    
    def test_proxy_connection(self, test_url: str = "https://httpbin.org/ip") -> bool:
        """
        Test proxy connection with a simple request.
        
        Args:
            test_url: URL to test connection with
            
        Returns:
            True if proxy connection works, False otherwise
        """
        if not self.proxy_config.enabled:
            return True
        
        try:
            import httpx
            
            proxies = self.get_httpx_proxies()
            auth = self.get_proxy_auth()
            
            with httpx.Client(proxies=proxies, auth=auth, timeout=10) as client:
                response = client.get(test_url)
                response.raise_for_status()
                
            logger.info("Proxy connection test successful")
            return True
            
        except Exception as e:
            logger.warning(f"Proxy connection test failed: {e}")
            return False
    
    def disable_proxy(self) -> None:
        """Disable proxy for this session."""
        self.proxy_config.enabled = False
        logger.info("Proxy disabled for this session")
    
    def enable_proxy(self, proxy_url: Optional[str] = None) -> None:
        """Enable proxy for this session."""
        if proxy_url:
            self.proxy_config = self._parse_proxy_url(proxy_url)
        else:
            # Reload from config/env
            self.proxy_config = self._load_proxy_config()
        
        if self.proxy_config.enabled:
            logger.info("Proxy enabled for this session")
        else:
            logger.warning("No proxy configuration found to enable")
    
    def get_proxy_info(self) -> Dict[str, Any]:
        """Get information about current proxy configuration."""
        if not self.proxy_config.enabled:
            return {"enabled": False}
        
        info = {
            "enabled": True,
            "http_proxy": self.proxy_config.http_proxy,
            "https_proxy": self.proxy_config.https_proxy,
            "has_auth": self.proxy_config.auth is not None
        }
        
        if self.proxy_config.auth:
            info["auth_username"] = self.proxy_config.auth[0]
            # Don't expose password in logs
        
        return info
