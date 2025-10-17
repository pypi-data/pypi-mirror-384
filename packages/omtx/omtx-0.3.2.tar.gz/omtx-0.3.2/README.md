# OMTX Python SDK

Lightweight helper for the OM Gateway. Queue diligence jobs, poll for results, and unlock/stream private data sets.

## Installation

```bash
pip install omtx
```

## Quick start

```python
from omtx import OMTXClient

client = OMTXClient()  # picks up OMTX_API_KEY

# 1) Generate claims (returns 202 + job_id)
claims_job = client.diligence_generate_claims(
    target="BRAF",
    prompt="Summarize known inhibitors"
)

# 2) Wait for the job and fetch the final payload
claims_result = client.wait_for_job(
    claims_job["job_id"],
    result_endpoint="/v2/jobs/generateClaims/{job_id}",
)
print("total claims:", claims_result["total_claims"])

# 3) Resynthesize report using a gene_key, auto-waiting for completion
report = client.diligence_synthesize_report(
    gene_key="acad8",
    wait=True,
)
print(report["sections"][0]["title"])

# 4) Deep research with automatic polling
deep = client.diligence_deep_research(
    query="CRISPR applications in cancer therapy",
    wait=True,
)
print(deep["final_report"][:400])
```

## Setup

### Get an API key

1. Sign up at [https://omtx.ai](https://omtx.ai)
2. Generate an API key from the dashboard

### Provide the API key

```bash
export OMTX_API_KEY="your-api-key"
```

The SDK defaults to the hosted gateway at `https://api-gateway-129153908223.us-central1.run.app`. If you need a different deployment, pass `base_url` explicitly (or set `OMTX_BASE_URL`).

Or pass both API key and base URL when constructing the client:

```python
from omtx import OMTXClient

client = OMTXClient(
    api_key="your-api-key",
    base_url="https://api-gateway-129153908223.us-central1.run.app",
)
```

## Usage examples

### Error handling and context manager

```python
from omtx import OMTXClient, InsufficientCreditsError, OMTXError

with OMTXClient() as client:
    try:
        report = client.diligence_synthesize_report(gene_key="acad8", wait=True)
    except InsufficientCreditsError:
        print("Add credits before running resynthesis jobs.")
    except OMTXError as exc:
        print(f"Gateway call failed: {exc}")
```

### Selective data access

```python
from omtx import OMTXClient

client = OMTXClient()

# 1) Unlock a dataset (consumes one Access Credit)
client.access_unlock(protein_uuid="aa11bb22", gene_name="KRAS")

# 2) Stream the private dataset
stream = client.data_access_selective_stream(
    dataset="private",
    protein_uuid="aa11bb22",
    limit=100_000,
    fmt="csv",
)

print("Rows:", stream.headers.get("X-Row-Count"))
with open("kras_selective.csv", "wb") as fh:
    for chunk in stream.iter_bytes():
        fh.write(chunk)
stream.close()
```

### Gene key discovery

```python
from omtx import OMTXClient

client = OMTXClient()
gene_keys = client.diligence_list_gene_keys(min_true=5)
print(gene_keys["items"][:5])
```

## Available helper methods

- `diligence_generate_claims(target, prompt, wait=False)`
- `diligence_synthesize_report(gene_key, wait=False)`
- `diligence_deep_research(query, wait=False, …)`
- `diligence_list_gene_keys(min_true=1, …)`
- `jobs_history(...)`, `job_status(job_id)`, `wait_for_job(job_id, …)`
- `access_unlock(protein_uuid, gene_name=None)`, `list_access_unlocks()`
- `data_access_selective_stream(...)`, `data_access_points_stream(...)`
- `data_access_selective_stats(...)`, `data_access_points_stats(...)`
- `credits()`, `health()`

## Requirements

- Python 3.9 or higher
- An OMTX API key

## Support

- Email: support@omtx.ai
- Docs: https://docs.omtx.ai
- Issues: https://github.com/omtx/python-sdk/issues

## License

MIT License – see `LICENSE` for details.
