from __future__ import annotations

import hashlib
from datetime import datetime, timezone
import json
import os
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests

from .exceptions import OMTXError
from ._internal.http import HTTPClient
from .endpoints import discover_endpoints
from sqlalchemy import update, func


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value, separators=(",", ":"), sort_keys=True, ensure_ascii=False
        )
    except Exception:
        return str(value)


def _derive_idempotency_key(
    user_key: Optional[str], method: str, path: str, body: Any
) -> str:
    if user_key and len(user_key) >= 8:
        return user_key
    # Generate a unique idempotency key using UUID + UTC date, hashed for uniformity
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    raw = f"{uuid.uuid4().hex}-{today}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass
class ClientConfig:
    base_url: str
    api_key: str
    timeout: int = 3600


class OMTXClient:
    """Thin SDK for Gateway V2.

    - base_url: e.g., http://localhost:8001
    - api_key: your x-api-key value
    - timeout: seconds for requests
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 3600,
    ):
        api_key = api_key or os.getenv("OMTX_API_KEY") or os.getenv("API_KEY")
        if not api_key:
            raise OMTXError(
                "API key is required. Pass api_key or set OMTX_API_KEY/API_KEY env var."
            )
        base_url = base_url or os.getenv("OMTX_BASE_URL") or "http://localhost:8001"
        if base_url.endswith("/"):
            base_url = base_url[:-1]
        self.cfg = ClientConfig(base_url=base_url, api_key=api_key, timeout=timeout)
        self._session = requests.Session()

    # ------------- Low-level HTTP -------------
    def _headers(self, idem_key: Optional[str]) -> Dict[str, str]:
        headers = {
            "x-api-key": self.cfg.api_key,
            "content-type": "application/json",
        }
        if idem_key:
            headers["idempotency-key"] = idem_key
        return headers

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        *,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        url = f"{self.cfg.base_url}{path}"
        body = body or {}
        idem = _derive_idempotency_key(idempotency_key, method, path, body)
        resp = self._session.request(
            method=method,
            url=url,
            headers=self._headers(idem),
            json=body if method != "GET" else None,
            params=body if method == "GET" else None,
            timeout=self.cfg.timeout,
        )
        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise OMTXError(f"HTTP {resp.status_code} for {path}: {detail}")
        try:
            return resp.json()
        except Exception:
            raise OMTXError("Non-JSON response")

    # ------------- Health -------------
    def health(self) -> Dict[str, Any]:
        return self._request("GET", "/v2/health", {})

    # ------------- Hits Catalog (protein-specific) -------------
    def hits_random(
        self, *, protein: str, n: int, idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/v2/hits-catalog/hits/random",
            {"protein": protein, "n": n},
            idempotency_key=idempotency_key,
        )

    def hits_sorted(
        self, *, protein: str, n: int, idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/v2/hits-catalog/hits/sorted",
            {"protein": protein, "n": n},
            idempotency_key=idempotency_key,
        )

    def decoys(
        self, *, protein: str, n: int, idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/v2/hits-catalog/decoys",
            {"protein": protein, "n": n},
            idempotency_key=idempotency_key,
        )

    def selective(
        self,
        *,
        positive: str,
        negative: str,
        n: int,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/v2/hits-catalog/selective",
            {"positive": positive, "negative": negative, "n": n},
            idempotency_key=idempotency_key,
        )

    def om_selective(
        self, *, protein: str, n: int, idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/v2/hits-catalog/om-selective",
            {"protein": protein, "n": n},
            idempotency_key=idempotency_key,
        )

    # ------------- Bioactive (global) -------------
    def bioactive_random(
        self, *, n: int, idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/v2/hits-catalog/bioactive/random",
            {"n": n},
            idempotency_key=idempotency_key,
        )

    def bioactive_random_sorted(
        self, *, n: int, idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/v2/hits-catalog/bioactive/random-sorted",
            {"n": n},
            idempotency_key=idempotency_key,
        )

    def bioactive_om_selective(
        self, *, n: int, idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/v2/hits-catalog/bioactive/om-selective",
            {"n": n},
            idempotency_key=idempotency_key,
        )

    def bioactive_om_selective_sorted(
        self, *, n: int, idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/v2/hits-catalog/bioactive/om-selective-sorted",
            {"n": n},
            idempotency_key=idempotency_key,
        )

    # ------------- Audit (free) -------------
    def audit_revealed(self, *, limit: int = 50) -> Dict[str, Any]:
        # GET path: no idempotency
        return self._request("GET", "/v2/hits-catalog/audit/revealed", {"limit": limit})

    def audit_check(
        self, *, products: list[str], idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/v2/hits-catalog/audit/check",
            {"products": products},
            idempotency_key=idempotency_key,
        )

    # ------------- Diligence (customer-facing) -------------
    def diligence_generate_claims(
        self, *, target: str, prompt: str, idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/v2/diligence/generateClaims",
            {"target": target, "prompt": prompt},
            idempotency_key=idempotency_key,
        )

    def diligence_synthesize_report(
        self, *, target: str, idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/v2/diligence/synthesizeReport",
            {"target": target},
            idempotency_key=idempotency_key,
        )

    def diligence_deep_research(
        self, *, query: str, idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/v2/diligence/deep-research",
            {"query": query},
            idempotency_key=idempotency_key,
        )

    def list_my_deep_research(self, *, limit: int = 20) -> Dict[str, Any]:
        """List my deep research results"""
        return self._request(
            "GET", "/v2/diligence/deep-research/history", {"limit": limit}
        )

    def list_my_claim_runs(self, *, limit: int = 20) -> Dict[str, Any]:
        """List my generateClaims results"""
        return self._request("GET", "/v2/diligence/claims/history", {"limit": limit})


"""Main OMTX client class"""


class Client:
    """OMTX API Client

    Simple client for interacting with the OM API Gateway.

    Args:
        api_key: Your API key. If not provided, uses OMTX_API_KEY environment variable.
        base_url: API base URL. Defaults to https://api.omtx.ai

    Example:
        >>> from omtx import Client
        >>> client = Client()
        >>> result = client.generate_diligence("BRAF")
        >>> print(result.summary)
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self._http = HTTPClient(api_key, base_url)
        self._register_endpoints()

    def _register_endpoints(self):
        """Dynamically register all endpoints as methods"""
        endpoints = discover_endpoints()

        for endpoint_class in endpoints.values():
            # Create instance of endpoint
            endpoint = endpoint_class()

            # Create method for this endpoint
            method = self._create_endpoint_method(endpoint)

            # Attach to client
            setattr(self, endpoint.name, method)

    def _create_endpoint_method(self, endpoint):
        """Create a method that calls an endpoint"""

        def method(*args, **kwargs):
            # Build request from user input
            request_data = endpoint.build_request(*args, **kwargs)

            # Make API call
            if endpoint.method == "GET":
                response_data = self._http.get(endpoint.path)
            else:
                response_data = self._http.post(endpoint.path, request_data)

            # Parse response
            return endpoint.parse_response(response_data)

        # Set metadata for better debugging/docs
        method.__name__ = endpoint.name
        method.__doc__ = endpoint.__doc__

        return method

    def credits(self) -> int:
        """Get available credits

        Returns:
            Number of available credits
        """
        # Credits is a simple GET endpoint
        response = self._http.get("/v2/credits")
        return response.get("available_credits", 0)

    def close(self):
        """Close the client and clean up resources"""
        self._http.close()

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up on context exit"""
        self.close()
