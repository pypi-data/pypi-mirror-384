"""Simple exception classes for OMTX SDK"""


class OMTXError(Exception):
    """Base exception for all OMTX errors"""
    pass


class AuthenticationError(OMTXError):
    """Raised when API key is invalid or missing"""
    pass


class InsufficientCreditsError(OMTXError):
    """Raised when user doesn't have enough credits"""
    
    def __init__(self, message: str, required: int = None, available: int = None):
        super().__init__(message)
        self.required = required
        self.available = available


class APIError(OMTXError):
    """Raised for API errors"""
    
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code