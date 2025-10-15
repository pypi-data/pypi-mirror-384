"""
Exception handling for AskPablos Scrapy API.

This module provides custom exceptions and error handling
utilities for the AskPablos Scrapy API middleware.
"""
from typing import Optional, Dict, Any


class AskPablosAPIError(Exception):
    """Base exception class for AskPablos API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        self.error_code = None

        # Extract error code from response if present
        if response and isinstance(response, dict):
            if 'error' in response:
                if isinstance(response['error'], dict):
                    self.error_code = response['error'].get('code')
                    # If the API provides a more detailed error message, use it
                    if response['error'].get('message'):
                        self.message = response['error']['message']
                elif isinstance(response['error'], str):
                    self.message = response['error']

        super().__init__(self.message)

    def __str__(self) -> str:
        """String representation of the error."""
        if self.status_code and self.error_code:
            return f"[{self.status_code}] {self.error_code}: {self.message}"
        elif self.status_code:
            return f"[{self.status_code}] {self.message}"
        else:
            return self.message


class AuthenticationError(AskPablosAPIError):
    """
    Raised when API key or secret key authentication fails.
    This is a critical error that should stop the spider.
    """

    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code, response)
        self.is_critical = True  # Flag to indicate this should stop the spider


class RateLimitError(AskPablosAPIError):
    """
    Raised when the API rate limit is exceeded.
    """

    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code, response)

        # Extract rate limit information if available
        self.reset_time = None
        self.limit = None
        self.remaining = None

        if response and isinstance(response, dict):
            rate_info = response.get('rateLimit', {})
            self.reset_time = rate_info.get('resetAt')
            self.limit = rate_info.get('limit')
            self.remaining = rate_info.get('remaining', 0)

    def __str__(self) -> str:
        """String representation with rate limit details if available."""
        base_str = super().__str__()
        if self.reset_time:
            return f"{base_str} (Limit: {self.limit}, Remaining: {self.remaining}, Reset at: {self.reset_time})"
        return base_str


class BrowserRenderingError(AskPablosAPIError):
    """
    Raised when there's an error with headless browser rendering.
    """
    pass


def handle_api_error(status_code: int, response_data: Optional[Dict[str, Any]] = None) -> Exception:
    """
    Factory function to create the appropriate exception based on status code.

    Args:
        status_code: HTTP status code
        response_data: API response data if available

    Returns:
        An appropriate Exception instance (built-in when possible)
    """
    message = "An error occurred with the AskPablos API"

    if response_data and isinstance(response_data, dict):
        error_data = response_data.get('error')
        if isinstance(error_data, dict) and 'message' in error_data:
            message = error_data['message']
        elif isinstance(error_data, str):
            message = error_data
        elif 'message' in response_data:
            message = response_data['message']

    if status_code == 401 or status_code == 403:
        return AuthenticationError(f"Authentication failed: {message}", status_code, response_data)
    elif status_code == 429:
        return RateLimitError(message, status_code, response_data)
    elif status_code == 408:
        return TimeoutError(f"[{status_code}] Request timed out: {message}")
    elif status_code == 400:
        return ValueError(f"[{status_code}] Invalid configuration: {message}")
    elif 400 <= status_code < 500:
        # Other client errors
        return ValueError(f"[{status_code}] Client error: {message}")
    elif status_code == 502 or status_code == 504:
        # Bad gateway or gateway timeout often related to proxy issues
        return ConnectionError(f"[{status_code}] Proxy error: {message}")
    elif 500 <= status_code < 600:
        # Server errors
        return RuntimeError(f"[{status_code}] Server error: {message}")
    else:
        return AskPablosAPIError(message, status_code, response_data)
