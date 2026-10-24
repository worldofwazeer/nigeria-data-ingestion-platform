# Implementation Decisions and Open Questions

This file records choices visible in the repository. It does not claim that each choice was formally approved. Items marked **Open question** need evidence or a deliberate decision before the implementation is extended.

## Choices reflected in the implementation

### Keep the active flow modular

**Evidence:** `app/main.py`, `app/pipeline.py`, `app/connectors/opaindex.py`, `app/api_client.py`, and `app/models/opaindex.py` separate command-line handling, orchestration, source access, transport, and validation. The README describes OpaIndex as the first active source.

**Current effect:** source-specific endpoint behavior is in the connector, while reusable HTTP behavior and response schema live in separate components.

### Use GET-only source retrieval with bounded status retries

**Evidence:** the connector calls `APIClient.get`; the client configures urllib3 retries for GET and HEAD, selected transient status codes, a configured retry total and backoff, and `Retry-After` support. Tests assert the policy and exercise success-after-retry and retry exhaustion.

**Current effect:** retry behavior is limited to configured statuses and allowed methods. It is not a general retry of every failure type.

### Validate the complete OpaIndex response with Pydantic

**Evidence:** the pipeline calls `OpaIndexResponse.model_validate`; models encode required fields, aliases, numeric bounds, and literal values; pipeline/model tests cover valid and invalid payloads.

**Current effect:** a payload that fails response validation does not produce a successful pipeline result. The code does not enforce `count == len(prices)`.

### Keep the older product exercise separate

**Evidence:** `learning_exercises/dummyjson_pipeline.py` is outside `app/` and has a product schema and separate extract/validate/transform flow. Its import path and `/prices` payload expectations differ from the active application.

**Current effect:** it is an isolated learning artifact, not a second active production pipeline.

### Do not contact the live service in unit tests

**Evidence:** the active test suite uses mocks for component behavior; retry tests use a loopback server. The README states that running `app.main` makes a real request.

**Current effect:** ordinary unit tests can run without service credentials or external availability.

## Open questions and assumptions

- **OpaIndex host and authentication:** `.env.example` contains a placeholder URL and describes the API key as optional. The repository does not establish the real host or whether the service requires a key. Verify externally before running the CLI.
- **Response contract:** field requirements reflect the checked-in Pydantic model, not independently verified provider documentation. Confirm the source contract before changing the model or asserting extra invariants.
- **Storage and downstream delivery:** neither is implemented. The target store, retention, idempotency, and delivery requirements remain undecided.
- **Pagination and incremental ingestion:** neither is implemented for the active connector. Supported query parameters and update semantics need source evidence first.
- **Invalid-record policy for future bulk ingestion:** the active pipeline validates one response model. The separate exercise drops invalid individual records, but that behavior is not evidence of the intended OpaIndex policy.
- **Learning exercise disposition:** its import and data-shape mismatches are visible, but the repository does not record whether it should be repaired or retained only as an archived example.
