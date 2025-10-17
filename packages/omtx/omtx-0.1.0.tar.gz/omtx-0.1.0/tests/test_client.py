"""Basic tests for OMTX client"""
import pytest
from unittest.mock import Mock, patch
from omtx import Client, OMTXError, InsufficientCreditsError


def test_client_requires_api_key():
    """Test that client requires an API key"""
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(OMTXError):
            Client()


def test_client_accepts_api_key():
    """Test that client accepts API key as parameter"""
    client = Client(api_key="test-key")
    assert client._http.api_key == "test-key"


def test_client_uses_env_var():
    """Test that client uses environment variable"""
    with patch.dict('os.environ', {'OMTX_API_KEY': 'env-key'}):
        client = Client()
        assert client._http.api_key == "env-key"


def test_credits_method():
    """Test credits method"""
    with patch('omtx._internal.http.HTTPClient.get') as mock_get:
        mock_get.return_value = {"available_credits": 1000}
        
        client = Client(api_key="test-key")
        credits = client.credits()
        
        assert credits == 1000
        mock_get.assert_called_once_with("/v2/credits")


def test_generate_diligence():
    """Test generate_diligence method"""
    with patch('omtx._internal.http.HTTPClient.post') as mock_post:
        mock_post.return_value = {
            "target": "BRAF",
            "status": "complete",
            "summary": {"target_summary": "BRAF is a protein..."}
        }
        
        client = Client(api_key="test-key")
        result = client.generate_diligence("BRAF")
        
        assert result.target == "BRAF"
        assert result.status == "complete"
        assert "BRAF is a protein" in result.summary
        
        # Check that the request was made correctly
        mock_post.assert_called_once_with(
            "/v2/diligence/generate",
            {"target": "BRAF"}
        )