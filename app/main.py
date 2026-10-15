"""Command-line entry point for fetching OpaIndex price data."""

import sys

from pydantic import ValidationError

from app.api_client import (
    APIClient,
    APIClientError,
    APIConnectionError,
    APIHTTPError,
    APITimeoutError,
    MalformedJSONError,
    UnexpectedMediaTypeError,
)
from app.pipeline import ingest_opaindex_prices


def main() -> int:
    try:
        with APIClient() as client:
            response = ingest_opaindex_prices(client)
    except APITimeoutError:
        print("Ingestion failed: request timed out.", file=sys.stderr)
        return 1
    except APIHTTPError as exc:
        print(f"Ingestion failed: OpaIndex returned HTTP {exc.status_code}.", file=sys.stderr)
        return 1
    except UnexpectedMediaTypeError:
        print("Ingestion failed: OpaIndex returned an unsupported response media type.", file=sys.stderr)
        return 1
    except MalformedJSONError:
        print("Ingestion failed: OpaIndex returned malformed JSON.", file=sys.stderr)
        return 1
    except APIConnectionError:
        print("Ingestion failed: could not connect to OpaIndex.", file=sys.stderr)
        return 1
    except APIClientError:
        print("Ingestion failed: the HTTP request could not be completed.", file=sys.stderr)
        return 1
    except ValidationError:
        print("Ingestion failed: OpaIndex response did not match the expected schema.", file=sys.stderr)
        return 1
    except ValueError as exc:
        # Configuration errors are constructed from fixed, non-secret messages.
        print(f"Ingestion failed: configuration error: {exc}.", file=sys.stderr)
        return 1
    except Exception as exc:
        # Avoid printing arbitrary exception text, which may contain request details.
        print(f"Ingestion failed: unexpected {type(exc).__name__}.", file=sys.stderr)
        return 1

    print(f"Fetched {response.count} OpaIndex price records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
