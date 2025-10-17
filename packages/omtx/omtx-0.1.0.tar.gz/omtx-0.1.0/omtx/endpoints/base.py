"""Base endpoint class for all API endpoints"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class Endpoint(ABC):
    """Base class for all endpoints"""
    
    # Subclasses must define these
    name: str = None  # Method name on client (e.g., "generate_diligence")
    path: str = None  # API path (e.g., "/v2/diligence/generate")
    method: str = "POST"  # HTTP method
    
    @abstractmethod
    def build_request(self, *args, **kwargs) -> Dict[str, Any]:
        """Transform user input into API request"""
        pass
    
    @abstractmethod
    def parse_response(self, data: Dict[str, Any]) -> Any:
        """Transform API response into user-friendly output"""
        pass