# Nigeria Data Ingestion Platform

World of Wazeer Data Ingestion and Tech Ventures is building a small, modular platform for collecting external data, validating its shape, and preserving source metadata. OpaIndex is the first active source. Storage and downstream transformations are not implemented yet.

## Current OpaIndex flow

The application fetches `/prices` through a reusable HTTP client, validates the response with Pydantic, and prints a concise record-count summary. Imports do not make network requests; network activity occurs only when the entry point is run.

```text
main → pipeline → OpaIndex connector → API client → OpaIndex response model
```

- `app/config.py`: environment-backed settings and validation
- `app/api_client.py`: shared HTTP session, retries, timeout, status checks, and JSON parsing
- `app/connectors/opaindex.py`: OpaIndex endpoint behavior
- `app/models/opaindex.py`: response and price-point contracts, aliases, decimals, provenance, confidence, and timestamps
- `app/pipeline.py`: coordinates fetching and validation
- `app/main.py`: application entry point

## Setup

Python 3.10 or newer is required.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Alternatively, `python -m pip install -r requirements.txt` installs runtime and test dependencies for local development.

## Configuration and credentials

Copy `.env.example` to `app/.env` for local configuration, then set `BASE_URL` to the OpaIndex API root. `.env` is ignored by Git. `API_KEY` is optional; leave it empty unless the service requires one. Timeout must be positive, retry count cannot be negative, and backoff cannot be negative. Never commit credentials or paste them into logs.

## Run and test

From the repository root:

```powershell
python -m app.main
python -m pytest
```

Unit tests use mocks and do not require the live API. Running `app.main` does make a real request.

## Learning exercise

`learning_exercises/dummyjson_pipeline.py` preserves an older product-data exercise separately from OpaIndex. It is not part of the active application. Its import still assumes a top-level `api_client`, and its extraction requests OpaIndex `/prices` while validating product-shaped records. Treat it as an archived learning example until those mismatches are deliberately resolved.

## Not implemented yet

- Persistent storage
- Normalization/transformation stages and downstream delivery
- Automated live-API integration tests
- Pagination or incremental ingestion for OpaIndex

The current response model follows the fields represented in the available implementation; it does not infer additional API guarantees such as `count == len(prices)`.
