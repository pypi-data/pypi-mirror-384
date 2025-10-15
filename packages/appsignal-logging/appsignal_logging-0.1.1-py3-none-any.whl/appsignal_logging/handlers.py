import json
import logging
import queue
import socket
import sys
import threading
from datetime import datetime, timezone
from typing import Set, Any

import httpx


# Default set of log record attributes to exclude from custom attributes
DEFAULT_EXCLUDED_LOG_ATTRIBUTES: Set[str] = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "lineno",
    "filename",
    "module",
    "funcName",
    "exc_info",
    "stack_info",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "process",
    "processName",
    "message",
}


class BaseAppSignalHandler(logging.Handler):
    """Base handler for AppSignal logging with common functionality."""

    def __init__(
        self,
        api_key: str,
        app_name: str | None = None,
        hostname: str | None = None,
        level: int = logging.NOTSET,
        excluded_attributes: Set[str] | None = None,
    ):
        super().__init__(level)
        self.api_key = api_key
        self.group = app_name
        self.hostname = hostname
        self.excluded_attributes = (
            excluded_attributes if excluded_attributes is not None else DEFAULT_EXCLUDED_LOG_ATTRIBUTES
        )
        self._queue: queue.Queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _extract_custom_attributes(self, record: logging.LogRecord) -> dict:
        """Extract custom attributes from log record, excluding standard fields."""
        attributes = {}

        for key, value in record.__dict__.items():
            if key in self.excluded_attributes:
                continue
            if isinstance(value, (str, int, float, bool)):
                attributes[key] = value

        return attributes

    def _log_error(self, message: str) -> None:
        """Log error to stderr."""
        print(f"Failed to send log to AppSignal: {message}", file=sys.stderr)

    def _worker(self):
        """Worker thread to process queue. Must be implemented by subclasses."""
        raise NotImplementedError

    def close(self):
        """Stop worker thread and wait for remaining messages to be processed."""
        self._stop_event.set()
        if self._thread.is_alive():
            timeout = getattr(self, "_close_timeout", 5.0)
            self._thread.join(timeout=timeout)
        super().close()


class AppSignalHTTPHandler(BaseAppSignalHandler):
    """
    A logging handler to send log messages to the AppSignal HTTP endpoint.
    https://docs.appsignal.com/logging/endpoints/http.html
    """

    def __init__(
        self,
        api_key: str,
        app_name: str | None = None,
        hostname: str | None = None,
        level: int = logging.NOTSET,
        excluded_attributes: Set[str] | None = None,
    ):
        super().__init__(api_key, app_name, hostname, level, excluded_attributes)
        self._url = self._build_url()
        self._headers = {"Content-Type": "application/json"}
        self._close_timeout = 5.0

    def _build_url(self):
        """Build AppSignal endpoint URL with query parameters."""
        url = f"https://appsignal-endpoint.net/logs?api_key={self.api_key}"
        if self.group:
            url += f"&group={self.group}"
        if self.hostname:
            url += f"&hostname={self.hostname}"
        return url

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            log_obj = {"message": msg}

            # Add custom attributes
            log_obj |= self._extract_custom_attributes(record)

            self._queue.put_nowait(json.dumps(log_obj))
        except Exception:
            self.handleError(record)

    def _worker(self):
        with httpx.Client(timeout=2.0) as client:
            # Main loop: wait for messages with timeout
            while not self._stop_event.is_set():
                try:
                    body = self._queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                self._send_log(client, body)

            # Drain remaining messages after stop event
            while True:
                try:
                    body = self._queue.get_nowait()
                except queue.Empty:
                    break
                self._send_log(client, body)

    def _send_log(self, client, body):
        """Send a single log message to AppSignal."""
        try:
            client.post(self._url, data=body, headers=self._headers)
        except Exception as e:
            self._log_error(str(e))


class AppSignalNDJSONHandler(BaseAppSignalHandler):
    """
    A logging handler to send log messages to the AppSignal NDJSON endpoint.
    Sends logs in batches using NDJSON format (Newline Delimited JSON).
    https://docs.appsignal.com/logging/endpoints/http-json.html

    This handler is more efficient for high-volume logging as it batches multiple
    log messages into a single HTTP request.
    """

    def __init__(
        self,
        api_key: str,
        app_name: str | None = None,
        hostname: str | None = None,
        level: int = logging.NOTSET,
        batch_size: int = 100,
        flush_interval: float = 5.0,
        excluded_attributes: Set[str] | None = None,
    ):
        # Set hostname before calling super().__init__
        if hostname is None:
            hostname = socket.gethostname()

        super().__init__(api_key, app_name, hostname, level, excluded_attributes)
        self._url = f"https://appsignal-endpoint.net/logs/json?api_key={self.api_key}"
        self._headers = {"Content-Type": "application/x-ndjson"}
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._close_timeout = 10.0

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)

            # Build NDJSON log object according to AppSignal spec
            log_obj: dict[str, Any] = {
                "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
                "message": msg,
                "severity": record.levelname.lower(),
            }

            if self.group:
                log_obj["group"] = self.group
            if self.hostname:
                log_obj["hostname"] = self.hostname

            # Extract custom attributes into separate 'attributes' field
            custom_attrs = self._extract_custom_attributes(record)
            if custom_attrs:
                log_obj["attributes"] = custom_attrs

            self._queue.put_nowait(log_obj)
        except Exception:
            self.handleError(record)

    def _worker(self):
        with httpx.Client(timeout=5.0) as client:
            batch = []
            last_flush = datetime.now()

            while not self._stop_event.is_set():
                try:
                    # Get log with timeout to allow periodic flushing
                    log_obj = self._queue.get(timeout=0.5)
                    batch.append(log_obj)

                    # Flush if batch is full
                    if len(batch) >= self._batch_size:
                        self._send_batch(client, batch)
                        batch = []
                        last_flush = datetime.now()

                except queue.Empty:
                    # Flush if interval passed
                    if batch and (datetime.now() - last_flush).total_seconds() >= self._flush_interval:
                        self._send_batch(client, batch)
                        batch = []
                        last_flush = datetime.now()

            # Drain remaining messages after stop event
            while True:
                try:
                    log_obj = self._queue.get_nowait()
                    batch.append(log_obj)
                except queue.Empty:
                    break

            # Final flush
            if batch:
                self._send_batch(client, batch)

    def _send_batch(self, client, batch):
        """Send a batch of log messages in NDJSON format."""
        try:
            # Convert batch to NDJSON (newline-delimited JSON)
            ndjson_body = "\n".join(json.dumps(log_obj) for log_obj in batch)
            client.post(self._url, data=ndjson_body, headers=self._headers)
        except Exception as e:
            self._log_error(str(e))
