# Learning Log

This log describes concepts represented in the current code and tests. The test results are recorded in [Project Status](PROJECT_STATUS.md).

## Concepts covered

### Reusable API client

`APIClient` centralizes HTTP behavior so the connector can describe which resource to fetch without owning session setup, headers, timeouts, or response parsing. Its context-manager methods close the Requests session even when an exception leaves the `with` block.

### Headers and credentials

The client sends a User-Agent and `Accept: application/json`; it adds an `X-API-Key` header only when an API key is configured. Tests assert both the default headers and optional key behavior. The `.env.example` value is a placeholder; it does not establish the real service host or authentication requirements.

### Timeouts and errors

Settings provide a positive default timeout, and a caller can override it for one request. The client converts Requests timeout and connection failures into project-specific exceptions and avoids embedding query strings in the safe endpoint used for error messages. HTTP failures after retries, unsupported media types, and malformed JSON have distinct error types. Entry-point tests check that expected failures produce safe messages and a nonzero result.

### JSON media types

The client checks the response `Content-Type` before parsing. It accepts `application/json` and structured suffix types such as `application/problem+json`, ignoring case and parameters. It rejects unrelated types that merely contain the word “json”, then separately reports malformed bodies labeled as JSON.

### Retry policy and real retry tests

The adapter retries GET and HEAD responses with status 429, 500, 502, 503, or 504. The configured retry total bounds attempts; backoff and `Retry-After` handling are enabled. Tests inspect the adapter policy and exercise both recovery after 503 and exhaustion after repeated 503 responses.

Those two retry tests use `ThreadingHTTPServer` bound to `127.0.0.1` on an ephemeral port. This is a real HTTP exchange confined to the local machine, not a live external API call. The helper shuts down and closes its server in cleanup.

### Pytest, mocks, and loopback servers

Mocks make isolated tests for session calls, response behavior, and component delegation without opening network connections. Pytest parameterization checks multiple media types and configuration failures. The local server is useful where a mock cannot prove the HTTP adapter actually retries requests.

### Pipeline validation

The connector returns raw JSON-shaped data; `ingest_opaindex_prices` then calls Pydantic validation. Tests cover successful conversion, invalid payloads, and propagation of connector failures. This separation makes extraction and schema validation distinct responsibilities.

## Next learning objectives

1. Confirm the source response contract before extending validation or inferring relationships between fields.
2. Decide and document how invalid records should be reported if ingestion later supports partial acceptance; current OpaIndex response validation rejects a response that does not match the model.
3. Design a small persistence stage with explicit idempotency and provenance requirements before implementing storage.
4. Revisit pagination and incremental ingestion only after the source API’s supported parameters and consistency behavior are verified.
5. Repair or clearly archive the older product exercise so its import path and requested data shape are consistent.
