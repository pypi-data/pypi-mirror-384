"""
Constants and configuration for YOPmail client.

This module contains all hardcoded values, URLs, and default configurations
used throughout the YOPmail client.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


# API Constants
BASE_URL = "https://yopmail.com"
VERSION = "9.2"
YJ_TOKEN = "AAGN1ZmL4AGxlZwLjZGN0ZQp"
AD_PARAM = 0

# Default Headers
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Request Headers
LOGIN_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://yopmail.com",
    "Referer": "https://yopmail.com/",
    "Cache-Control": "max-age=0",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
}

INBOX_HEADERS = {
    "Referer": "https://yopmail.com/wm",
    "Sec-Fetch-Dest": "iframe",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
}

SEND_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://yopmail.com",
    "Referer": "https://yopmail.com/wm",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9,de-DE;q=0.8,de;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=1, i",
}

# Default Cookie Values (updated with fresh browser session - October 14, 2025)
DEFAULT_COOKIES = {
    "ytime": "0:18",  # Updated time from real browser session
    "yc": "EAGNlBGD2Awx4ZmpkZGN4ZQV",
    "yses": "zz6dtenHstru+L/GLPPQD4a5iJbTzoLzBsyP3HkfhNIwBQRWRdGPgRYto8uoBVoi",
    # Fresh anti-bot cookies from latest browser session
    "FCNEC": "%5B%5B%22AKsRol_6F42HOVxM6EaK5AzHHz6pBZ_s5IEy0SEsxyy-uoiU8y8_xL4dEzrZFin7v--j4O2_PFq0BRr3_VLVsDP3GGZGL2OsU1ZWEokkR_RZ_jBrvi4Xp4fFvcD1SJdlzRJsLemj_U5VBJ7SdrdAe49PIX4OE2eYyA%3D%3D%22%5D%5D",
    "FCCDCF": "%5Bnull%2Cnull%2Cnull%2C%5B%22CQWjP4AQWjP4AEsACBENB5FoAP_gAEPgAAqIK1IB_C7EbCFCiDp3IKMEMAhHABBAYsAwAAYBAwAADBIQIAQCgkEYBASAFCACCAAAKASBAAAgCAAAAUAAIAAVAABAAAwAIBAIIAAAgAAAAEAIAAAACIAAEQCAAAAEAEAAkAgAAAIASAAAAAAAAACBAAAAAAAAAAAAAAAABAAAAQAAQAAAAAAAiAAAAAAAABAIAAAAAAAAAAAAAAAAAAAAAAgAAAAAAAAAABAAAAAAAQR2QD-F2I2EKFEHCuQUYIYBCuACAAxYBgAAwCBgAAGCQgQAgFJIIkCAEAIEAAEAAAQAgCAABQEBAAAIAAAAAqAACAABgAQCAQQIABAAAAgIAAAAAAEQAAIgEAAAAIAIABABAAAAQAkAAAAAAAAAECAAAAAAAAAAAAAAAAAAAAAEABgAAAAAABEAAAAAAAACAQIAAA.cAAAAAAAAAA%22%2C%222~61.89.122.184.196.230.314.442.445.494.550.576.827.1029.1033.1046.1047.1051.1097.1126.1166.1301.1342.1415.1725.1765.1942.1958.1987.2068.2072.2074.2107.2213.2219.2223.2224.2328.2331.2387.2416.2501.2567.2568.2575.2657.2686.2778.2869.2878.2908.2920.2963.3005.3023.3100.3126.3219.3234.3235.3253.3309.3731.6931.8931.13731.15731~dv.%22%2C%220300B232-3BBA-4065-9DF9-FA0EF3FB75D7%22%5D%5D",
    # Additional cookies from fresh session
    "compte": "testuserauto2:righthandpath:testuserauto3:testuserx:testuserauto1:test_agent_a_20251012t221230z:test_agent_b_20251012t221230z:owner:advertiser:asdhsdaq",
    "__eoi": "ID=35600ad0fb561277:T=1755902461:RT=1760393936:S=AA-AfjbMAapjaFGpb5UM0DMBDBj6",
    "__gads": "ID=50e1fb970662d3ce:T=1755902461:RT=1760393936:S=ALNI_MY3XfyUKaP7QZR4LLOzYjceTyPLsg",
    "__gpi": "UID=0000126838c12cc0:T=1755902461:RT=1758731437:S=ALNI_MZv-G62t2o_oOP7-v_-_5Odq56sWA",
    "ywm": "testuserauto2",
}

# API Endpoints
ENDPOINTS = {
    "main": "/",
    "wm": "/en/wm",
    "inbox": "/inbox",
    "mail": "/mail",
    "send": "/writepost",
    "rss": "/rss",
    "gen_rss": "/gen-rss",
}

# CSS Selectors
SELECTORS = {
    "yp_token": "input#yp",
    "message": ".m",
    "subject": ".lsub, .lms",
    "sender": ".lmf",
    "time": ".lmh",
}

# Rate Limiting Constants
RATE_LIMIT_STATUS_CODES = [429, 503, 502, 504]
RATE_LIMIT_HEADERS = ["Retry-After", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
DEFAULT_RATE_LIMIT_DELAY = 5.0  # seconds
MAX_RATE_LIMIT_DELAY = 300.0  # 5 minutes max

# Proxy Configuration
PROXY_ENV_VARS = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]
PROXY_CONFIG_KEYS = ["proxy", "proxies", "proxy_url", "proxy_host", "proxy_port"]

# Default Configuration
@dataclass
class Config:
    """Configuration class for YOPmail client."""
    base_url: str = BASE_URL
    timeout: int = 30
    language: str = "en"
    follow_redirects: bool = True
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Rate limiting settings
    rate_limit_detection: bool = True
    rate_limit_delay: float = DEFAULT_RATE_LIMIT_DELAY
    max_rate_limit_delay: float = MAX_RATE_LIMIT_DELAY
    
    # Proxy settings
    proxy_url: Optional[str] = None
    proxy_host: Optional[str] = None
    proxy_port: Optional[int] = None
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None
    proxy_enabled: bool = False

DEFAULT_CONFIG = Config()

# Message Parsing Constants
MESSAGE_PREFIX = "i"  # Prefix for message IDs in mail endpoint
