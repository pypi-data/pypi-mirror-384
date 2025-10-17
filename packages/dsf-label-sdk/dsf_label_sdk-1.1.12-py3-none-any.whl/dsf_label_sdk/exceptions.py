# dsf_label_sdk/exceptions.py
"""Custom exceptions for the SDK"""

from typing import Optional 

class LabelSDKError(Exception):
    """Base exception for SDK errors."""
    pass


class ValidationError(LabelSDKError):
    """Raised when input validation fails."""
    pass


class LicenseError(LabelSDKError):
    """Raised when license validation fails."""
    pass


class APIError(LabelSDKError):
    """Raised when API request fails."""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class RateLimitError(APIError):
    """Raised when rate limited (429)"""
    def __init__(self, message: str, retry_after: int = 60, limit: int = None):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after
        self.limit = limit