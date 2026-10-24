# Project Status

## Verified milestone

The active OpaIndex path is implemented through a reusable HTTP client, a `/prices` connector, Pydantic response validation, and a command-line summary. The client handles configured headers and timeouts, selected HTTP status retries, response status errors, JSON media-type validation, malformed JSON, and connection failures. API-client tests include mocks and real local loopback HTTP responses to exercise retry success and exhaustion.

This is an ingestion and validation milestone only. No persistence, downstream delivery, OpaIndex pagination, or incremental ingestion is implemented.

## Current working tree

At the start of this documentation task, Git reported:

```text
 M app/api_client.py
 M tests/test_api_client.py
```

These are pre-existing unstaged modifications and were preserved. Documentation changes from this task are expected in `README.md` and `docs/`. Nothing was staged, committed, or pushed.

## Latest recorded test results

The latest results available in the referenced project chat (not rerun for this documentation task) were:

- `tests/test_api_client.py`: **23 passed**.
- Full test suite: **46 passed**.

The earlier targeted run reported one pytest cache warning because access to `.pytest_cache` was denied. The results above are historical reports, not a fresh verification of the current working tree.

## Known issues and limits

- `learning_exercises/dummyjson_pipeline.py` imports `api_client` as a top-level module, while the active client lives at `app.api_client`.
- That exercise fetches `/prices` but validates product-shaped records; it is separate from the active OpaIndex pipeline and is not documented as runnable.
- OpaIndex response assumptions are limited to fields encoded in `app/models/opaindex.py`; no source contract evidence in this repository confirms extra invariants such as `count == len(prices)`.
- There is no persistence, transformation/delivery stage, pagination, incremental ingestion, or automated live-service test coverage.
- The configured OpaIndex API host and its live behavior are not verified by the repository; `.env.example` contains a placeholder.

## Recommended next steps

1. Review the existing `app/api_client.py` and `tests/test_api_client.py` changes together, preserving their current unstaged state until explicitly ready to accept them.
2. Decide whether to repair, relabel more clearly, or retire the mismatched learning exercise without coupling it to production-oriented OpaIndex code.
3. Confirm the OpaIndex response contract from an authoritative source before changing model assumptions or adding pagination.
4. Choose a small next learning milestone, such as improving pipeline validation/error reporting or designing persistence, and add behavior tests before implementation.

Do not run `python -m app.main` as a unit-test substitute: it contacts the configured external service.
