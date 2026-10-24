# Nigeria Data Ingestion Platform

A small Python project for learning and building a modular data ingestion platform. OpaIndex is the active source integration. The current application fetches price data, validates its shape, and prints a record count; it does not persist or transform the data for downstream use.

## Current capability

The application performs a GET request to the configured OpaIndex API root plus `/prices`. A shared HTTP client applies configured headers, timeout and status retry policy, checks response status and JSON media type, and parses JSON. The pipeline validates that payload against Pydantic response and price-point models. The command-line entry point prints the validated record count and reports safe error messages.

```text
main → pipeline → OpaIndex connector → API client → JSON → Pydantic response model
```

Imports do not make network requests. Running the application does make a real request to the configured service.

## Setup

Python 3.10 or newer is required. From the repository root, create and activate a virtual environment, then install the development extra:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Alternatively, `python -m pip install -r requirements.txt` installs the listed runtime and test dependencies.

## Configuration

Copy `.env.example` to `app/.env` and set `BASE_URL` to the actual OpaIndex API root. The example value is only a placeholder, not a verified service host. `API_KEY` is optional in the code and is sent as `X-API-Key` when supplied. `TIMEOUT` must be greater than zero; `MAX_RETRIES` and `BACKOFF_FACTOR` must be nonnegative. `.env` files are ignored by Git. Keep credentials out of source control and logs.

## Run safely

Run the unit tests from the repository root; the suite uses mocks and a local loopback HTTP server for retry behavior, so it does not require a live API:

```powershell
python -m pytest
```

Running the application reaches the configured external API. Use it only after confirming that `BASE_URL` is a real endpoint you intend to contact:

```powershell
python -m app.main
```

## Project map

- `app/config.py` loads and validates environment-backed settings.
- `app/api_client.py` configures the reusable Requests session, headers, retries, timeout, HTTP errors, and JSON response handling.
- `app/connectors/opaindex.py` requests the `/prices` endpoint.
- `app/models/opaindex.py` defines the response and price-point validation contracts, including field aliases, decimal values, provenance, confidence, and timestamps.
- `app/pipeline.py` coordinates extraction and validation.
- `app/main.py` is the command-line entry point and maps failures to safe messages.
- `learning_exercises/dummyjson_pipeline.py` is a separate older exercise, not part of the active OpaIndex application.
- `docs/` contains the current status, architecture, learning log, and implementation decisions.

## Known limits

- No persistent storage, downstream delivery, or active normalization/transformation stage is implemented.
- OpaIndex pagination and incremental ingestion are not implemented.
- There are no automated live-service integration tests; unit tests do not establish the actual service contract or availability.
- The OpaIndex model validates represented fields but does not enforce an inferred relationship such as `count == len(prices)`.
- The older learning exercise imports a top-level `api_client` and requests OpaIndex `/prices` while validating product-shaped records. Those mismatches are unresolved; treat it as a learning reference, not a runnable active pipeline.

For verified status and follow-up work, see [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md). For data flow details, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
