"""Environment-backed application settings."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

@dataclass(frozen=True)
class Settings:
    """Validated settings used to configure the HTTP client."""

    base_url: str
    api_key: str | None = None
    timeout: float = 15.0
    max_retries: int = 3
    backoff_factor: float = 2.0

    @classmethod
    def from_environment(cls) -> "Settings":
        """Load and validate settings from environment variables and `.env`."""
        load_dotenv()

        base_url_value = os.getenv("BASE_URL", "").strip().rstrip("/")
        if not base_url_value:
            raise ValueError("BASE_URL is required; set it in the environment or app/.env")
        if not base_url_value.startswith(("http://", "https://")):
            raise ValueError("BASE_URL must be an absolute HTTP or HTTPS URL")

        try:
            timeout = float(os.getenv("TIMEOUT", "15"))
            max_retries = int(os.getenv("MAX_RETRIES", "3"))
            backoff_factor = float(os.getenv("BACKOFF_FACTOR", "2"))
        except ValueError as exc:
            raise ValueError(
                "TIMEOUT and BACKOFF_FACTOR must be numbers, and "
                "MAX_RETRIES must be an integer"
            ) from exc

        if timeout <= 0:
            raise ValueError("TIMEOUT must be greater than zero")
        if max_retries < 0:
            raise ValueError("MAX_RETRIES cannot be negative")
        if backoff_factor < 0:
            raise ValueError("BACKOFF_FACTOR cannot be negative")

        api_key = os.getenv("API_KEY")
        return cls(
            base_url=base_url_value,
            api_key=api_key if api_key else None,
            timeout=timeout,
            max_retries=max_retries,
            backoff_factor=backoff_factor,
        )
