# AppSignal Logging for Python

[![PyPI version](https://badge.fury.io/py/appsignal-logging.svg)](https://badge.fury.io/py/appsignal-logging)
[![Python Support](https://img.shields.io/pypi/pyversions/appsignal-logging.svg)](https://pypi.org/project/appsignal-logging/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Python logging handlers for [AppSignal](https://www.appsignal.com/) with support for both simple HTTP and high-performance NDJSON batch endpoints.

## Features

- 🚀 **Two handler types**: Simple HTTP and batched NDJSON
- 📦 **Automatic batching**: Efficiently send multiple logs in a single request
- ⚡ **High performance**: Up to 10x faster than sending individual logs
- 🔄 **Async worker thread**: Non-blocking log transmission
- 🛡️ **Error handling**: Graceful failure with stderr logging
- 🏷️ **Structured logging**: Support for custom attributes
- 📝 **Type hints**: Full type annotation support
- ✅ **Well tested**: Comprehensive test suite

## Installation

```bash
pip install appsignal-logging
```

## Quick Start

### Simple HTTP Handler

Best for low-frequency logging (<10 logs/sec):

```python
import logging
from appsignal_logging import AppSignalHTTPHandler

handler = AppSignalHTTPHandler(
    api_key="your_api_key",
    app_name="my_app",
    hostname="web-server-1"
)

logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)

logger.info("User logged in", extra={"user_id": 123, "ip": "192.168.1.1"})
```

### NDJSON Handler (Recommended for Production)

Best for high-frequency logging (>100 logs/sec):

```python
import logging
from appsignal_logging import AppSignalNDJSONHandler

handler = AppSignalNDJSONHandler(
    api_key="your_api_key",
    app_name="my_app",
    hostname="web-server-1",
    batch_size=100,        # Send every 100 logs
    flush_interval=5.0     # Or every 5 seconds
)

logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)

logger.info("User logged in", extra={"user_id": 123, "ip": "192.168.1.1"})
```

## Handler Comparison

| Feature | HTTP Handler | NDJSON Handler |
|---------|-------------|----------------|
| **Requests per 1000 logs** | 1000 | 10-20 |
| **Latency** | ~0.5s | 0-5s |
| **Memory usage** | Low | Medium |
| **Network load** | High | Low |
| **Performance** | Low at >100 logs/sec | High |
| **Best for** | Dev/Low traffic | Production/High traffic |

## Configuration Options

### AppSignalHTTPHandler

```python
AppSignalHTTPHandler(
    api_key: str,              # Required: Your AppSignal API key
    app_name: str = None,      # Optional: Application name
    hostname: str = None,      # Optional: Hostname (auto-detected if not provided)
    level: int = logging.NOTSET  # Optional: Minimum log level
)
```

### AppSignalNDJSONHandler

```python
AppSignalNDJSONHandler(
    api_key: str,              # Required: Your AppSignal API key
    app_name: str = None,      # Optional: Application name
    hostname: str = None,      # Optional: Hostname (auto-detected if not provided)
    level: int = logging.NOTSET,  # Optional: Minimum log level
    batch_size: int = 100,     # Optional: Logs per batch (default: 100)
    flush_interval: float = 5.0  # Optional: Flush interval in seconds (default: 5.0)
)
```

## Advanced Usage

### Custom Attributes

Add custom attributes to your logs using the `extra` parameter:

```python
logger.info(
    "Payment processed",
    extra={
        "user_id": 123,
        "amount": 99.99,
        "currency": "USD",
        "transaction_id": "txn_123456"
    }
)
```

### Multiple Handlers

Use different handlers for different log levels:

```python
# Critical errors go immediately via HTTP
critical_handler = AppSignalHTTPHandler(
    api_key="your_api_key",
    app_name="my_app"
)
critical_handler.setLevel(logging.ERROR)

# Info logs batched via NDJSON
info_handler = AppSignalNDJSONHandler(
    api_key="your_api_key",
    app_name="my_app",
    batch_size=200
)
info_handler.setLevel(logging.INFO)

logger = logging.getLogger()
logger.addHandler(critical_handler)
logger.addHandler(info_handler)
```

### Django Integration

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'appsignal': {
            'class': 'appsignal_logging.AppSignalNDJSONHandler',
            'api_key': 'your_api_key',
            'app_name': 'myapp',
            'level': 'INFO',
            'batch_size': 100,
            'flush_interval': 5.0,
        },
    },
    'root': {
        'handlers': ['appsignal'],
        'level': 'INFO',
    },
}
```

## Requirements

- Python 3.8+
- httpx >= 0.24.0

## Development

```bash
# Clone the repository
git clone https://github.com/yourusername/appsignal-logging-python.git
cd appsignal-logging-python

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=appsignal_logging --cov-report=html

# Format code
black src tests

# Lint code
ruff check src tests

# Type check
mypy src
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Links

- [AppSignal Documentation](https://docs.appsignal.com/logging/)
- [PyPI Package](https://pypi.org/project/appsignal-logging/)
- [GitHub Repository](https://github.com/magicjohnson/appsignal-logging-python)
- [Issue Tracker](https://github.com/magicjohnson/appsignal-logging-python/issues)

## Acknowledgments

- Built for [AppSignal](https://www.appsignal.com/)
- Inspired by the need for efficient Python logging in production environments
