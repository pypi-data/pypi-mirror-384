"""
Custom exceptions for the PayStation SDK.
"""

class PayStationException(Exception):
    """Base exception for PayStation SDK."""
    pass

class APIError(PayStationException):
    """Raised when the API returns an error."""
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API Error {status_code}: {message}")
