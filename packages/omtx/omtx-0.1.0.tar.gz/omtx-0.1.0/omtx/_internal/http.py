"""Internal HTTP client with automatic retry and idempotency"""
import os
import time
import uuid
from typing import Dict, Any, Optional
import httpx
from ..exceptions import OMTXError, AuthenticationError, InsufficientCreditsError, APIError


class HTTPClient:
    """Handles all HTTP communication with the OM API Gateway"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or os.environ.get("OMTX_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "API key required. Pass api_key to Client() or set OMTX_API_KEY environment variable"
            )
        
        self.base_url = base_url or os.environ.get("OMTX_API_URL", "https://api.omtx.ai")
        self.client = httpx.Client(timeout=60.0)
    
    def request(self, method: str, path: str, json: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP request with automatic retry and idempotency"""
        # Generate idempotency key for non-GET requests
        headers = {"X-API-Key": self.api_key}
        if method != "GET":
            headers["Idempotency-Key"] = str(uuid.uuid4())
        
        url = f"{self.base_url}{path}"
        
        # Retry logic with exponential backoff
        last_error = None
        for attempt in range(3):
            try:
                response = self.client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json
                )
                
                # Handle successful responses
                if response.status_code == 200:
                    return response.json()
                
                # Handle specific error codes
                if response.status_code == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status_code == 402:
                    raise InsufficientCreditsError("Insufficient credits")
                elif response.status_code == 404:
                    raise OMTXError(f"Endpoint not found: {path}")
                elif response.status_code >= 500:
                    # Server error - retry
                    last_error = APIError(
                        f"Server error: {response.text}", 
                        status_code=response.status_code
                    )
                    if attempt < 2:  # Don't sleep on last attempt
                        time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    # Other client errors
                    try:
                        error_detail = response.json().get("detail", response.text)
                    except:
                        error_detail = response.text
                    raise APIError(error_detail, status_code=response.status_code)
                    
            except httpx.NetworkError as e:
                # Network error - retry
                last_error = OMTXError(f"Network error: {str(e)}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
                continue
        
        # All retries failed
        raise last_error or OMTXError("Request failed after 3 attempts")
    
    def get(self, path: str) -> Dict[str, Any]:
        """GET request"""
        return self.request("GET", path)
    
    def post(self, path: str, json: Dict[str, Any]) -> Dict[str, Any]:
        """POST request"""
        return self.request("POST", path, json)
    
    def close(self):
        """Close the HTTP client"""
        self.client.close()