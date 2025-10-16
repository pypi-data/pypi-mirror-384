This module serves as a central place for providing utilities for our Python backends.

To install the package, run:
```bash
pip install crypticorn-utils
```
or for development:
```bash
pip install -e .[dev]
```

- **Auth**: Authentication and authorization for APIs with API key, JWT bearer token, and basic auth support
- **Exceptions**: Comprehensive error handling system with HTTP/WebSocket exceptions and standardized error responses
- **Logging**: Logging configuration and utilities for consistent formatting across services
- **Middleware**: API middleware components for request/response processing
- **Pagination**: Utilities for paginated API responses with cursor-based pagination, filtering, and sorting
- **Metrics**: Prometheus metrics collection for HTTP requests, response times, and sizes
- **Types**: Environment definitions (prod/dev/local/docker) and base URL management
- **Utils**: General utility functions including random ID generation, datetime conversion, and optional imports
