# Architecture

## Active OpaIndex flow

```text
app.main
  → app.pipeline.ingest_opaindex_prices
    → app.connectors.opaindex.OpaIndexConnector.fetch_prices
      → app.api_client.APIClient.get
        → configured HTTP session → response status/media-type/JSON checks
    → app.models.opaindex.OpaIndexResponse.model_validate
  → print validated record count
```

The entry point owns command-line behavior and translates expected client, configuration, and Pydantic failures into concise messages. It uses `APIClient` as a context manager so the underlying session is closed on success or failure.

## Component responsibilities

- **Settings (`app/config.py`)**: reads `BASE_URL`, optional `API_KEY`, `TIMEOUT`, `MAX_RETRIES`, and `BACKOFF_FACTOR` from the environment (and `.env` via `python-dotenv`). It checks required URL presence, HTTP(S) prefix, and numeric bounds.
- **Transport (`app/api_client.py`)**: builds a Requests session with a user-agent and JSON accept header, adds `X-API-Key` when configured, mounts HTTP adapters with an urllib3 retry policy, applies the default or per-call timeout, and maps connection, timeout, HTTP, content-type, and JSON parse failures to client exceptions.
- **Connector (`app/connectors/opaindex.py`)**: defines the source-specific `/prices` path and delegates the GET request to the shared client. It returns raw JSON-shaped data without model validation.
- **Pipeline (`app/pipeline.py`)**: calls the connector and validates its raw result as `OpaIndexResponse`. Validation failures propagate to the entry point.
- **Models (`app/models/opaindex.py`)**: describe response and price-point fields. Pydantic aliases map `dayChangePercent`, `weekChangePercent`, and `asOf` input keys to Python attributes. Prices and changes use `Decimal`; confidence and response source are constrained literals.
- **Entry point (`app/main.py`)**: performs one ingestion, prints the record count, and returns a nonzero status with safe messages on failure.

## Request and retry behavior visible in code

The connector issues a GET for `/prices` against `BASE_URL`. The client configures retries for status codes 429, 500, 502, 503, and 504 on GET and HEAD, using `MAX_RETRIES`, `BACKOFF_FACTOR`, and `Retry-After` when provided. The client disables raising from the adapter after retry exhaustion so it can raise its own `APIHTTPError` with the endpoint and final status code. These settings describe implementation behavior; they do not guarantee how the external service responds.

After a successful HTTP status, the client accepts `application/json` and `application/*+json` media types (case-insensitively, with parameters allowed), then parses the response body as JSON. The pipeline subsequently validates the payload. No storage or downstream output is present.

## Test boundaries

Tests under `tests/` cover settings, the HTTP client, connector delegation, model validation, pipeline orchestration, and safe entry-point errors. The client tests use mocked sessions/responses for most cases and a loopback HTTP server for actual retry behavior. They do not call the live OpaIndex API or verify its availability or undocumented response guarantees.

## Separate learning exercise

`learning_exercises/dummyjson_pipeline.py` contains its own product models and extraction/validation/transformation functions. It imports a top-level `api_client`, requests `/prices`, and expects product-shaped values. This differs from the active package structure and OpaIndex response contract, so it is not part of the active flow.
