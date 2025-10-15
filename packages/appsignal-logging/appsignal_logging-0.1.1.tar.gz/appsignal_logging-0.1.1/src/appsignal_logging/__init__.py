"""
AppSignal Logging for Python
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Python logging handlers for AppSignal with HTTP and NDJSON support.

Basic usage:

   >>> import logging
   >>> from appsignal_logging import AppSignalNDJSONHandler
   >>>
   >>> handler = AppSignalNDJSONHandler(
   ...     api_key="your_api_key",
   ...     app_name="my_app"
   ... )
   >>> logger = logging.getLogger()
   >>> logger.addHandler(handler)
   >>> logger.info("Hello AppSignal!")

:copyright: (c) 2025
:license: MIT, see LICENSE for more details.
"""

__version__ = "0.1.1"
__author__ = "Dmitriy Trochshenko"
__license__ = "MIT"

from .handlers import (
    AppSignalHTTPHandler,
    AppSignalNDJSONHandler,
    DEFAULT_EXCLUDED_LOG_ATTRIBUTES,
)

__all__ = [
    "AppSignalHTTPHandler",
    "AppSignalNDJSONHandler",
    "DEFAULT_EXCLUDED_LOG_ATTRIBUTES",
    "__version__",
]
