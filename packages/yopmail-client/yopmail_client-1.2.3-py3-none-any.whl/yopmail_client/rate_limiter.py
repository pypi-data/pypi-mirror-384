"""
Rate limiting detection and management for YOPmail client.

This module handles automatic detection of rate limiting responses
and implements intelligent retry logic with exponential backoff.
"""

import time
import logging
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from .exceptions import YOPMailError, HTTPError
from .constants import (
    RATE_LIMIT_STATUS_CODES, 
    RATE_LIMIT_HEADERS,
    DEFAULT_RATE_LIMIT_DELAY,
    MAX_RATE_LIMIT_DELAY
)

logger = logging.getLogger(__name__)


@dataclass
class RateLimitInfo:
    """Information about rate limiting."""
    is_rate_limited: bool
    retry_after: Optional[float] = None
    remaining_requests: Optional[int] = None
    reset_time: Optional[datetime] = None
    delay_seconds: float = DEFAULT_RATE_LIMIT_DELAY


class RateLimiter:
    """Handles rate limiting detection and retry logic."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize rate limiter with configuration."""
        self.config = config
        self.rate_limit_detection = config.get("rate_limit_detection", True)
        self.base_delay = config.get("rate_limit_delay", DEFAULT_RATE_LIMIT_DELAY)
        self.max_delay = config.get("max_rate_limit_delay", MAX_RATE_LIMIT_DELAY)
        self.last_request_time = 0.0
        self.consecutive_rate_limits = 0
        
    def detect_rate_limit(self, status_code: int, headers: Dict[str, str], response_text: str = "") -> RateLimitInfo:
        """
        Detect if the response indicates rate limiting.
        
        Args:
            status_code: HTTP status code
            headers: Response headers
            response_text: Response body text
            
        Returns:
            RateLimitInfo object with rate limiting details
        """
        if not self.rate_limit_detection:
            return RateLimitInfo(is_rate_limited=False)
        
        # Check status code
        is_rate_limited = status_code in RATE_LIMIT_STATUS_CODES
        
        # Check for rate limiting indicators in response
        if not is_rate_limited and response_text:
            rate_limit_indicators = [
                "rate limit", "too many requests", "quota exceeded",
                "throttled", "slow down", "try again later"
            ]
            response_lower = response_text.lower()
            is_rate_limited = any(indicator in response_lower for indicator in rate_limit_indicators)
        
        if not is_rate_limited:
            return RateLimitInfo(is_rate_limited=False)
        
        # Extract rate limiting information
        retry_after = self._extract_retry_after(headers)
        remaining_requests = self._extract_remaining_requests(headers)
        reset_time = self._extract_reset_time(headers)
        
        # Calculate delay
        delay_seconds = self._calculate_delay(retry_after, remaining_requests)
        
        logger.warning(f"Rate limit detected: {status_code}, delay: {delay_seconds}s")
        
        return RateLimitInfo(
            is_rate_limited=True,
            retry_after=retry_after,
            remaining_requests=remaining_requests,
            reset_time=reset_time,
            delay_seconds=delay_seconds
        )
    
    def _extract_retry_after(self, headers: Dict[str, str]) -> Optional[float]:
        """Extract Retry-After header value."""
        retry_after = headers.get("Retry-After", headers.get("retry-after"))
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                logger.debug(f"Invalid Retry-After header: {retry_after}")
        return None
    
    def _extract_remaining_requests(self, headers: Dict[str, str]) -> Optional[int]:
        """Extract remaining requests from headers."""
        remaining = headers.get("X-RateLimit-Remaining", headers.get("x-ratelimit-remaining"))
        if remaining:
            try:
                return int(remaining)
            except ValueError:
                logger.debug(f"Invalid X-RateLimit-Remaining header: {remaining}")
        return None
    
    def _extract_reset_time(self, headers: Dict[str, str]) -> Optional[datetime]:
        """Extract rate limit reset time from headers."""
        reset_timestamp = headers.get("X-RateLimit-Reset", headers.get("x-ratelimit-reset"))
        if reset_timestamp:
            try:
                # Try Unix timestamp first
                timestamp = float(reset_timestamp)
                return datetime.fromtimestamp(timestamp)
            except ValueError:
                try:
                    # Try ISO format
                    return datetime.fromisoformat(reset_timestamp.replace('Z', '+00:00'))
                except ValueError:
                    logger.debug(f"Invalid X-RateLimit-Reset header: {reset_timestamp}")
        return None
    
    def _calculate_delay(self, retry_after: Optional[float], remaining_requests: Optional[int]) -> float:
        """Calculate appropriate delay based on rate limit information."""
        # Use Retry-After header if available
        if retry_after:
            return min(retry_after, self.max_delay)
        
        # Use exponential backoff based on consecutive rate limits
        if self.consecutive_rate_limits > 0:
            delay = self.base_delay * (2 ** min(self.consecutive_rate_limits, 6))  # Cap at 2^6
            return min(delay, self.max_delay)
        
        # Use base delay
        return self.base_delay
    
    def should_retry(self, rate_limit_info: RateLimitInfo) -> bool:
        """Determine if we should retry after rate limiting."""
        if not rate_limit_info.is_rate_limited:
            self.consecutive_rate_limits = 0
            return False
        
        # Check if we've exceeded max retries
        if self.consecutive_rate_limits >= 5:  # Max 5 consecutive rate limits
            logger.error("Too many consecutive rate limits, giving up")
            return False
        
        return True
    
    def wait_for_retry(self, rate_limit_info: RateLimitInfo) -> None:
        """Wait for the appropriate time before retrying."""
        if not rate_limit_info.is_rate_limited:
            return
        
        delay = rate_limit_info.delay_seconds
        logger.info(f"Rate limited, waiting {delay:.1f} seconds before retry...")
        
        # Add some jitter to avoid thundering herd
        jitter = delay * 0.1 * (0.5 - time.time() % 1)  # ±10% jitter
        actual_delay = max(0, delay + jitter)
        
        time.sleep(actual_delay)
        self.consecutive_rate_limits += 1
        self.last_request_time = time.time()
    
    def handle_rate_limit(self, status_code: int, headers: Dict[str, str], response_text: str = "") -> Tuple[bool, float]:
        """
        Handle rate limiting detection and return retry decision.
        
        Args:
            status_code: HTTP status code
            headers: Response headers
            response_text: Response body text
            
        Returns:
            Tuple of (should_retry, delay_seconds)
        """
        rate_limit_info = self.detect_rate_limit(status_code, headers, response_text)
        
        if not rate_limit_info.is_rate_limited:
            self.consecutive_rate_limits = 0
            return False, 0.0
        
        if not self.should_retry(rate_limit_info):
            raise HTTPError(
                status_code, 
                "Rate limit exceeded", 
                f"Too many consecutive rate limits. Last delay: {rate_limit_info.delay_seconds}s"
            )
        
        return True, rate_limit_info.delay_seconds
    
    def get_request_delay(self) -> float:
        """Get delay needed before next request to avoid rate limiting."""
        if self.last_request_time == 0:
            return 0.0
        
        time_since_last = time.time() - self.last_request_time
        min_interval = 1.0  # Minimum 1 second between requests
        
        if time_since_last < min_interval:
            return min_interval - time_since_last
        
        return 0.0
    
    def record_request(self) -> None:
        """Record that a request was made."""
        self.last_request_time = time.time()
    
    def reset(self) -> None:
        """Reset rate limiter state."""
        self.consecutive_rate_limits = 0
        self.last_request_time = 0.0
