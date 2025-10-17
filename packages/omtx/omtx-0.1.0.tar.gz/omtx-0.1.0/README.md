# OMTX Python SDK

Simple Python client for the OM API Gateway. Generate molecular diligence reports and perform deep scientific research with just a few lines of code.

## Installation

```bash
pip install omtx
```

## Quick Start

```python
from omtx import Client

# Initialize client (uses OMTX_API_KEY environment variable)
client = Client()

# Generate a diligence report
result = client.generate_diligence("BRAF")
print(result.summary)

# Perform deep research
research = client.deep_research("CRISPR applications in cancer treatment")
print(research.final_report)

# Check available credits
credits = client.credits()
print(f"Available credits: {credits}")
```

## Setup

### Get an API Key

1. Sign up at [https://omtx.ai](https://omtx.ai)
2. Navigate to your dashboard
3. Generate an API key

### Set Your API Key

#### Option 1: Environment Variable (Recommended)

```bash
export OMTX_API_KEY="your-api-key-here"
```

#### Option 2: Pass to Client

```python
from omtx import Client

client = Client(api_key="your-api-key-here")
```

## Examples

### Generate Diligence Report

```python
from omtx import Client

client = Client()

# Generate report for a molecular target
result = client.generate_diligence("KRAS")

# Access the summary
print(result.summary)

# Access full report data
print(result.report_data)
```

### Deep Research

```python
from omtx import Client

client = Client()

# Perform deep research on a scientific query
research = client.deep_research(
    "CAR-T therapy mechanisms and recent advances",
    max_iterations=5  # Optional: more iterations = deeper research
)

# View the final report
print(research.final_report)

# Access individual findings
for finding in research.findings:
    print(f"- {finding['claim']}")

# Check execution time
print(f"Research completed in {research.execution_time:.1f} seconds")
```

### Error Handling

```python
from omtx import Client, OMTXError, InsufficientCreditsError

client = Client()

try:
    result = client.generate_diligence("BRAF")
except InsufficientCreditsError as e:
    print(f"Not enough credits. Please add more credits to your account.")
except OMTXError as e:
    print(f"An error occurred: {e}")
```

### Context Manager

```python
from omtx import Client

# Automatically cleans up resources
with Client() as client:
    result = client.generate_diligence("TP53")
    print(result.summary)
```

## Available Methods

- `generate_diligence(target)` - Generate a comprehensive diligence report for a molecular target
- `deep_research(query, max_iterations=3)` - Perform iterative deep research on a scientific query
- `credits()` - Check available credits

## Features

- **Simple API** - Just a few methods to remember
- **Automatic Retries** - Handles transient network errors automatically
- **Idempotency** - Safe to retry requests without double charges
- **Type Hints** - Full IDE autocomplete support
- **Error Handling** - Clear, actionable error messages

## Requirements

- Python 3.8 or higher
- An OMTX API key

## Support

- Email: support@omtx.ai
- Documentation: https://docs.omtx.ai
- Issues: https://github.com/omtx/python-sdk/issues

## License

MIT License - see LICENSE file for details.