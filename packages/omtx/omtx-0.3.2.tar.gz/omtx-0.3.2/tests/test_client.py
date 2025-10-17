from __future__ import annotations

import os
import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from omtx import OMTXClient, OMTXError
from omtx.client import JobTimeoutError


def make_response(status: int, payload: dict | str):
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status
    if isinstance(payload, dict):
        resp.json.return_value = payload
        resp.content = json_bytes = json.dumps(payload).encode("utf-8")
        resp.text = json_bytes.decode("utf-8")
    else:
        resp.json.side_effect = ValueError
        resp.text = payload
        resp.content = payload.encode("utf-8")
    return resp


def test_requires_api_key():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(OMTXError):
            OMTXClient()


def test_uses_env_api_key():
    with patch.dict(os.environ, {"OMTX_API_KEY": "env-key"}):
        client = OMTXClient(base_url="https://example.com")
        assert client.cfg.api_key == "env-key"
        client.close()


@patch("omtx.client.requests.Session.request")
def test_diligence_synthesize_report_gene_key(mock_request):
    mock_request.return_value = make_response(202, {"job_id": "job-123"})
    client = OMTXClient(api_key="key", base_url="https://example.com")

    resp = client.diligence_synthesize_report(gene_key="acad8")
    assert resp["job_id"] == "job-123"

    kwargs = mock_request.call_args.kwargs
    assert kwargs["method"] == "POST"
    assert kwargs["json"] == {"gene_key": "acad8"}
    assert kwargs["url"].endswith("/v2/diligence/synthesizeReport")


@patch("omtx.client.requests.Session.request")
def test_access_unlock_payload(mock_request):
    mock_request.return_value = make_response(
        200, {"unlocked": True, "protein_uuid": "uuid"}
    )
    client = OMTXClient(api_key="key", base_url="https://example.com")

    client.access_unlock(protein_uuid="uuid", gene_name="TP53")

    kwargs = mock_request.call_args.kwargs
    assert kwargs["method"] == "POST"
    assert kwargs["json"] == {"protein_uuid": "uuid", "gene_name": "TP53"}
    assert kwargs["url"].endswith("/v2/access/unlock")


def test_wait_for_job_success():
    client = OMTXClient(api_key="key", base_url="https://example.com")
    client.job_status = MagicMock(
        side_effect=[
            {"job_id": "abc", "status": "queued"},
            {"job_id": "abc", "status": "succeeded"},
        ]
    )
    client._request = MagicMock(return_value={"result": "ok"})

    with patch("omtx.client.time.sleep", return_value=None):
        result = client.wait_for_job(
            "abc", result_endpoint="/v2/jobs/foo/{job_id}", poll_interval=0.01
        )

    assert result == {"result": "ok"}
    client._request.assert_called_with("GET", "/v2/jobs/foo/abc", {})


def test_wait_for_job_timeout():
    client = OMTXClient(api_key="key", base_url="https://example.com")
    client.job_status = MagicMock(return_value={"status": "queued"})

    with patch("omtx.client.time.sleep", return_value=None):
        with pytest.raises(JobTimeoutError):
            client.wait_for_job("abc", poll_interval=0.01, timeout=0.05)


@patch("omtx.client.requests.Session.request")
def test_list_gene_keys(mock_request):
    mock_request.return_value = make_response(
        200, {"items": [{"gene_key": "acad8", "true_count": 42}]}
    )
    client = OMTXClient(api_key="key", base_url="https://example.com")

    resp = client.diligence_list_gene_keys(min_true=5, limit=10)
    assert resp["items"][0]["gene_key"] == "acad8"

    kwargs = mock_request.call_args.kwargs
    assert kwargs["method"] == "GET"
    assert kwargs["params"] == {"min_true": 5, "limit": 10, "offset": 0}


@patch("omtx.client.requests.Session")
def test_context_manager_closes(mock_session_cls):
    mock_session = mock_session_cls.return_value
    mock_resp = make_response(202, {"job_id": "job-1"})
    mock_session.request.return_value = mock_resp

    with OMTXClient(api_key="key", base_url="https://example.com") as client:
        client.diligence_generate_claims(target="TP53", prompt="summary")

    mock_session.close.assert_called_once()
