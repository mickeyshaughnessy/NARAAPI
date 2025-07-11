# NARAAPI
NARA API

This is a simple records-mirroring interface for governments.

It provides the public with easy, safe and inexpensive access to goverment archive services & raw records, ensuring redactions and differential privacy injection are carried out faithfully.

It also contains a crawler (crawler.py) for making authenticated requests to agency backend APIs.

It also contains placeholders for nonpublic countermeasures and countercountermeasures devices.


# NARA API Server

A generic API server with data privacy features for querying archives, filtering, redacting names, and applying differential privacy.

## Features

- Token-based authentication
- Archive querying with filtering and pagination
- Data redaction capabilities for PII protection
- Differential privacy implementation
- Request logging and audit trails
- OpenAPI documentation

## Project Structure

- `api_server.py` - Main server application
- `api_endpoints.py` - API endpoint definitions
- `handlers.py` - Data processing handlers
- `utils.py` - Utility functions and Redis client
- `config.py` - Server configuration
- `int_tests.py` - Integration tests
  `crawler.py` - Backend crawler, asshole

## Setup

1. Install dependencies:
```bash
pip install flask flask-cors redis numpy
```

2. Configure Redis:
Edit `config.py` to set your Redis connection parameters.

3. Run the server:
```bash
python api_server.py
```

## API Documentation

API documentation is available at `/api/docs` when the server is running.

## Testing

Run integration tests:
```bash
python int_tests.py
```
