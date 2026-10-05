# Nigeria External Data Ingestion & Integration Platform

Production-oriented backend system built under **World of Wazeer** for acquiring, validating, normalizing, and analyzing external Nigerian datasets.

## Architecture Overview
- **Data Acquisition**: Resilient HTTP/API client with exponential backoff and connection pooling.
- **Validation & Data Contracts**: Schema enforcement via Pydantic models.
- **Storage & Analytics**: PostgreSQL persistence for raw and normalized data layers.

## Domain Focus
- Primary Domain: Agriculture (Market prices, macro indicators, weather patterns).
