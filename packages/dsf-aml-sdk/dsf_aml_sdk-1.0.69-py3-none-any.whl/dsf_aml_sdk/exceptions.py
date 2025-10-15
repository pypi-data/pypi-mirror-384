# ============================================
# dsf_aml_sdk/exceptions.py
# ============================================
from typing import Optional

class AMLSDKError(Exception):
    pass

class ValidationError(AMLSDKError):
    pass

class LicenseError(AMLSDKError):
    pass

class APIError(AMLSDKError):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __str__(self):
        if self.status_code:
            return f"APIError ({self.status_code}): {self.message}"
        return f"APIError: {self.message}"
    
class RateLimitError(AMLSDKError):
    """Raised when API returns 429 with Retry-After header."""
    def __init__(self, message: str = "Rate limited", retry_after: int = 60, status_code: int = 429):
        super().__init__(message)
        self.message = message
        self.retry_after = int(retry_after)
        self.status_code = status_code

    def __str__(self):
        return f"RateLimitError: {self.message} (retry after {self.retry_after}s)"