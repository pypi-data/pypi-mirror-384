"""OMTX Python SDK - Clients for OM Gateway V2.

Includes:
- OMTXClient: Simple, explicit client with idempotency and typed methods
- Client: Dynamic endpoint registry alternative (advanced)
"""

from .client import OMTXClient, Client
from .exceptions import OMTXError, InsufficientCreditsError, AuthenticationError

__version__ = "0.1.0"
__all__ = [
    "OMTXClient",
    "Client",
    "OMTXError",
    "InsufficientCreditsError",
    "AuthenticationError",
]
