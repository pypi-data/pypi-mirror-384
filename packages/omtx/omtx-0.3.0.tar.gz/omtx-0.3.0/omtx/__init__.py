"""OMTX Python SDK - Client for OM Gateway V2.

Includes:
- OMTXClient: Explicit client with automatic idempotency and typed methods
"""

from .client import OMTXClient, JobTimeoutError
from .exceptions import OMTXError, InsufficientCreditsError, AuthenticationError

__version__ = "0.3.0"
__all__ = [
    "OMTXClient",
    "OMTXError",
    "InsufficientCreditsError",
    "AuthenticationError",
    "JobTimeoutError",
]
