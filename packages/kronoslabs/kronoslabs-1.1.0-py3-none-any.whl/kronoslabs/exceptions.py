"""
Custom exceptions for Kronos Labs API
"""


class KronosLabsError(Exception):
    """Base exception for Kronos Labs API errors"""
    pass


class APIError(KronosLabsError):
    """Raised when API returns an error response"""
    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AuthenticationError(KronosLabsError):
    """Raised when authentication fails"""
    pass
