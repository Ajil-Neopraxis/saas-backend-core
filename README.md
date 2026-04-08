# SaaS Backend Core

Core backend package for SaaS applications providing JWE authentication, API clients, MongoDB integration, and BigCommerce integration.

## Installation

```bash
pip install git+https://github.com/Ajil-Neopraxis/saas-backend-core.git@main
```

## Features

- **JWE Authentication**: JWT with Encryption for secure token handling
- **API Clients**: Base API client for external service communication
- **MongoDB**: Async MongoDB connection and repository pattern
- **BigCommerce**: Client for BigCommerce API operations
- **SaaS App**: Client for SaaS platform API

## Usage

```python
from backend_core import create_auth_router, SaasAppAPIClient, connect_to_mongo

# Authentication
auth_router = create_auth_router(
    secret_key="your-secret-key",
    issuer="your-issuer",
    audience="your-audience"
)

# SaaS App Client
client = SaasAppAPIClient(
    base_url="https://api.example.com",
    token="your-api-token"
)
```

## API Reference

### Authentication
- `create_auth_router()` - Create FastAPI auth router with JWE token handling

### API Clients
- `BaseAPIClient` - Base HTTP client
- `SaasAppAPIClient` - SaaS platform API client
- `BigCommerceClient` - BigCommerce API client

### MongoDB
- `connect_to_mongo()` - Connect to MongoDB
- `get_database()` - Get database instance
- `BaseRepository` - Base repository class

### JWE
- `create_auth_jwe_token()` - Create JWE token
- `decrypt_auth_jwe_token()` - Decrypt JWE token
- `validate_jwe_payload()` - Validate token payload
- `refresh_auth_token()` - Refresh expiring token
