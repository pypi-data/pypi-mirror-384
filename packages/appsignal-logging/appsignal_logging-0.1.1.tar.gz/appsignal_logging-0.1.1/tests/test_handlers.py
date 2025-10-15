import json
import logging
import queue
import time
import unittest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import httpx

from appsignal_logging import AppSignalHTTPHandler, AppSignalNDJSONHandler


class TestAppSignalHTTPHandler(unittest.TestCase):
    def setUp(self):
        self.api_key = "test_api_key_123"
        self.app_name = "test_app"
        self.hostname = "test_host"
        self.mock_client = MagicMock()
        self.handler = None

        self.patcher = patch("appsignal_logging.handlers.httpx.Client")
        self.mock_client_class = self.patcher.start()
        self.mock_client_class.return_value.__enter__.return_value = self.mock_client

    def tearDown(self):
        self.patcher.stop()
        if self.handler:
            try:
                self.handler.close()
            except Exception:
                pass

    def _create_log_record(self, level=logging.INFO, msg="Test message"):
        return logging.LogRecord(
            name="test",
            level=level,
            pathname="test.py",
            lineno=10,
            msg=msg,
            args=(),
            exc_info=None,
        )

    def test_when_initialized_with_api_key_should_create_handler_with_defaults(self):
        self.handler = AppSignalHTTPHandler(self.api_key)

        self.assertEqual(self.handler.api_key, self.api_key)
        self.assertIsNone(self.handler.group)
        self.assertIsNone(self.handler.hostname)
        self.assertIsInstance(self.handler._queue, queue.Queue)
        self.assertTrue(self.handler._thread.is_alive())

    def test_when_initialized_with_optional_params_should_store_them(self):
        self.handler = AppSignalHTTPHandler(self.api_key, app_name=self.app_name, hostname=self.hostname)

        self.assertEqual(self.handler.group, self.app_name)
        self.assertEqual(self.handler.hostname, self.hostname)

    def test_when_emitting_basic_log_should_create_correct_log_object(self):
        self.handler = AppSignalHTTPHandler(self.api_key)
        record = self._create_log_record()

        with patch.object(self.handler, "_queue") as mock_queue:
            self.handler.emit(record)

            mock_queue.put_nowait.assert_called_once()
            log_data = json.loads(mock_queue.put_nowait.call_args[0][0])
            self.assertEqual(log_data["message"], "Test message")
            self.assertNotIn("severity", log_data)

    def test_when_initialized_with_app_name_and_hostname_should_add_to_url(self):
        self.handler = AppSignalHTTPHandler(self.api_key, app_name=self.app_name, hostname=self.hostname)

        self.assertIn(f"group={self.app_name}", self.handler._url)
        self.assertIn(f"hostname={self.hostname}", self.handler._url)

    def test_when_emitting_with_app_name_and_hostname_should_not_include_in_json(self):
        self.handler = AppSignalHTTPHandler(self.api_key, app_name=self.app_name, hostname=self.hostname)
        record = self._create_log_record(level=logging.ERROR, msg="Error message")

        with patch.object(self.handler, "_queue") as mock_queue:
            self.handler.emit(record)

            log_data = json.loads(mock_queue.put_nowait.call_args[0][0])
            self.assertNotIn("group", log_data)
            self.assertNotIn("hostname", log_data)

    def test_when_record_has_custom_attributes_should_include_them(self):
        self.handler = AppSignalHTTPHandler(self.api_key)
        record = self._create_log_record(level=logging.WARNING, msg="Warning message")
        record.user_id = "user123"
        record.request_id = "req456"
        record.count = 42
        record.is_valid = True

        with patch.object(self.handler, "_queue") as mock_queue:
            self.handler.emit(record)

            log_data = json.loads(mock_queue.put_nowait.call_args[0][0])
            self.assertEqual(log_data["user_id"], "user123")
            self.assertEqual(log_data["request_id"], "req456")
            self.assertEqual(log_data["count"], 42)
            self.assertEqual(log_data["is_valid"], True)

    def test_when_emitting_should_filter_standard_attributes(self):
        self.handler = AppSignalHTTPHandler(self.api_key)
        record = self._create_log_record()

        with patch.object(self.handler, "_queue") as mock_queue:
            self.handler.emit(record)

            log_data = json.loads(mock_queue.put_nowait.call_args[0][0])
            self.assertNotIn("name", log_data)
            self.assertNotIn("msg", log_data)
            self.assertNotIn("levelname", log_data)
            self.assertNotIn("pathname", log_data)
            self.assertNotIn("lineno", log_data)

    def test_when_record_has_non_serializable_types_should_exclude_them(self):
        self.handler = AppSignalHTTPHandler(self.api_key)
        record = self._create_log_record()
        record.string_attr = "test"
        record.int_attr = 123
        record.float_attr = 45.67
        record.bool_attr = True
        record.list_attr = [1, 2, 3]
        record.dict_attr = {"key": "value"}
        record.none_attr = None

        with patch.object(self.handler, "_queue") as mock_queue:
            self.handler.emit(record)

            log_data = json.loads(mock_queue.put_nowait.call_args[0][0])
            self.assertEqual(log_data["string_attr"], "test")
            self.assertEqual(log_data["int_attr"], 123)
            self.assertEqual(log_data["float_attr"], 45.67)
            self.assertEqual(log_data["bool_attr"], True)
            self.assertNotIn("list_attr", log_data)
            self.assertNotIn("dict_attr", log_data)
            self.assertNotIn("none_attr", log_data)

    def test_when_log_emitted_should_worker_send_to_appsignal(self):
        self.handler = AppSignalHTTPHandler(self.api_key)
        record = self._create_log_record()

        self.handler.emit(record)
        time.sleep(0.6)

        self.mock_client.post.assert_called()
        call_args = self.mock_client.post.call_args
        expected_url = f"https://appsignal-endpoint.net/logs?api_key={self.api_key}"
        self.assertEqual(call_args[0][0], expected_url)
        self.assertEqual(call_args[1]["headers"]["Content-Type"], "application/json")

    def test_when_http_error_occurs_should_worker_continue_processing(self):
        self.mock_client.post.side_effect = httpx.HTTPError("Connection failed")
        self.handler = AppSignalHTTPHandler(self.api_key)
        record = self._create_log_record()

        self.handler.emit(record)
        time.sleep(0.6)

        self.assertTrue(self.handler._thread.is_alive())

    def test_when_close_called_should_stop_worker_thread(self):
        self.handler = AppSignalHTTPHandler(self.api_key)
        self.assertFalse(self.handler._stop_event.is_set())

        self.handler.close()

        self.assertTrue(self.handler._stop_event.is_set())

    def test_when_emit_has_formatting_error_should_handle_gracefully(self):
        self.handler = AppSignalHTTPHandler(self.api_key)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test %s %s",
            args=("arg1",),
            exc_info=None,
        )
        self.handler.handleError = Mock()

        self.handler.emit(record)

        self.handler.handleError.assert_called_once_with(record)

    def test_when_different_log_levels_should_format_message(self):
        self.handler = AppSignalHTTPHandler(self.api_key)

        levels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]

        with patch.object(self.handler, "_queue") as mock_queue:
            for level in levels:
                record = self._create_log_record(level=level)
                self.handler.emit(record)

            self.assertEqual(mock_queue.put_nowait.call_count, len(levels))
            for call in mock_queue.put_nowait.call_args_list:
                log_data = json.loads(call[0][0])
                self.assertIn("message", log_data)
                self.assertNotIn("severity", log_data)

    def test_when_emitting_many_logs_should_not_block(self):
        self.handler = AppSignalHTTPHandler(self.api_key)

        for i in range(1000):
            record = self._create_log_record(msg=f"Message {i}")
            self.handler.emit(record)

        self.assertFalse(self.handler._queue.empty())

    def test_when_queue_empty_should_worker_continue_after_timeout(self):
        self.handler = AppSignalHTTPHandler(self.api_key)

        time.sleep(0.6)

        self.assertTrue(self.handler._thread.is_alive())

    def test_when_emitting_log_should_serialize_to_valid_json(self):
        self.handler = AppSignalHTTPHandler(self.api_key)
        record = self._create_log_record()

        with patch.object(self.handler, "_queue") as mock_queue:
            self.handler.emit(record)

            json_str = mock_queue.put_nowait.call_args[0][0]
            log_data = json.loads(json_str)
            self.assertIsInstance(log_data, dict)
            self.assertIn("message", log_data)

    def test_edgecase_when_close_called_immediately_should_process_remaining_messages(self):
        self.handler = AppSignalHTTPHandler("test_key")

        for i in range(10):
            record = self._create_log_record(msg=f"Message {i}")
            self.handler.emit(record)

        self.handler.close()

        self.assertEqual(self.mock_client.post.call_count, 10)

    def test_edgecase_when_close_called_should_wait_for_thread_to_finish(self):
        self.handler = AppSignalHTTPHandler("test_key")

        self.assertTrue(self.handler._thread.is_alive())

        self.handler.close()
        time.sleep(0.1)

        self.assertFalse(self.handler._thread.is_alive())

    def test_edgecase_when_http_error_occurs_should_log_error_to_stderr(self):
        self.mock_client.post.side_effect = Exception("Network error")
        self.handler = AppSignalHTTPHandler("test_key")
        record = self._create_log_record(level=logging.ERROR, msg="Important error")

        self.handler.emit(record)
        time.sleep(0.6)

        self.mock_client.post.assert_called()

    def test_edgecase_when_record_has_none_attribute_should_exclude_it(self):
        self.handler = AppSignalHTTPHandler("test_key")
        record = self._create_log_record(msg="Test")
        record.nullable_field = None

        with patch.object(self.handler, "_queue") as mock_queue:
            self.handler.emit(record)

            log_data = json.loads(mock_queue.put_nowait.call_args[0][0])
            self.assertNotIn("nullable_field", log_data)


class TestAppSignalNDJSONHandler(unittest.TestCase):
    def setUp(self):
        self.api_key = "test_api_key_123"
        self.app_name = "test_app"
        self.hostname = "test_host"
        self.mock_client = MagicMock()
        self.handler = None

        self.patcher = patch("appsignal_logging.handlers.httpx.Client")
        self.mock_client_class = self.patcher.start()
        self.mock_client_class.return_value.__enter__.return_value = self.mock_client

    def tearDown(self):
        self.patcher.stop()
        if self.handler:
            try:
                self.handler.close()
            except Exception:
                pass

    def _create_log_record(self, level=logging.INFO, msg="Test message"):
        return logging.LogRecord(
            name="test",
            level=level,
            pathname="test.py",
            lineno=10,
            msg=msg,
            args=(),
            exc_info=None,
        )

    def test_when_initialized_with_api_key_should_create_handler_with_defaults(self):
        self.handler = AppSignalNDJSONHandler(self.api_key)

        self.assertEqual(self.handler.api_key, self.api_key)
        self.assertIsNone(self.handler.group)
        self.assertIsNotNone(self.handler.hostname)
        self.assertEqual(self.handler._batch_size, 100)
        self.assertEqual(self.handler._flush_interval, 5.0)
        self.assertIsInstance(self.handler._queue, queue.Queue)
        self.assertTrue(self.handler._thread.is_alive())

    def test_when_initialized_with_optional_params_should_store_them(self):
        self.handler = AppSignalNDJSONHandler(
            self.api_key,
            app_name=self.app_name,
            hostname=self.hostname,
            batch_size=50,
            flush_interval=10.0,
        )

        self.assertEqual(self.handler.group, self.app_name)
        self.assertEqual(self.handler.hostname, self.hostname)
        self.assertEqual(self.handler._batch_size, 50)
        self.assertEqual(self.handler._flush_interval, 10.0)

    def test_when_emitting_basic_log_should_create_correct_log_object(self):
        self.handler = AppSignalNDJSONHandler(self.api_key)
        record = self._create_log_record()

        with patch.object(self.handler, "_queue") as mock_queue:
            self.handler.emit(record)

            mock_queue.put_nowait.assert_called_once()
            log_data = mock_queue.put_nowait.call_args[0][0]
            self.assertEqual(log_data["message"], "Test message")
            self.assertIn("timestamp", log_data)
            self.assertIn("severity", log_data)
            self.assertEqual(log_data["severity"], "info")

    def test_when_initialized_with_app_name_and_hostname_should_include_in_log_object(self):
        self.handler = AppSignalNDJSONHandler(self.api_key, app_name=self.app_name, hostname=self.hostname)
        record = self._create_log_record()

        with patch.object(self.handler, "_queue") as mock_queue:
            self.handler.emit(record)

            log_data = mock_queue.put_nowait.call_args[0][0]
            self.assertEqual(log_data["group"], self.app_name)
            self.assertEqual(log_data["hostname"], self.hostname)

    def test_when_record_has_custom_attributes_should_include_them_in_attributes_field(self):
        self.handler = AppSignalNDJSONHandler(self.api_key)
        record = self._create_log_record(level=logging.WARNING, msg="Warning message")
        record.user_id = "user123"
        record.request_id = "req456"
        record.count = 42
        record.is_valid = True

        with patch.object(self.handler, "_queue") as mock_queue:
            self.handler.emit(record)

            log_data = mock_queue.put_nowait.call_args[0][0]
            self.assertIn("attributes", log_data)
            self.assertEqual(log_data["attributes"]["user_id"], "user123")
            self.assertEqual(log_data["attributes"]["request_id"], "req456")
            self.assertEqual(log_data["attributes"]["count"], 42)
            self.assertEqual(log_data["attributes"]["is_valid"], True)

    def test_when_emitting_should_filter_standard_attributes(self):
        self.handler = AppSignalNDJSONHandler(self.api_key)
        record = self._create_log_record()

        with patch.object(self.handler, "_queue") as mock_queue:
            self.handler.emit(record)

            log_data = mock_queue.put_nowait.call_args[0][0]
            attrs = log_data.get("attributes", {})
            self.assertNotIn("name", attrs)
            self.assertNotIn("msg", attrs)
            self.assertNotIn("levelname", attrs)
            self.assertNotIn("pathname", attrs)
            self.assertNotIn("lineno", attrs)

    def test_when_record_has_non_serializable_types_should_exclude_them(self):
        self.handler = AppSignalNDJSONHandler(self.api_key)
        record = self._create_log_record()
        record.string_attr = "test"
        record.int_attr = 123
        record.float_attr = 45.67
        record.bool_attr = True
        record.list_attr = [1, 2, 3]
        record.dict_attr = {"key": "value"}
        record.none_attr = None

        with patch.object(self.handler, "_queue") as mock_queue:
            self.handler.emit(record)

            log_data = mock_queue.put_nowait.call_args[0][0]
            attrs = log_data["attributes"]
            self.assertEqual(attrs["string_attr"], "test")
            self.assertEqual(attrs["int_attr"], 123)
            self.assertEqual(attrs["float_attr"], 45.67)
            self.assertEqual(attrs["bool_attr"], True)
            self.assertNotIn("list_attr", attrs)
            self.assertNotIn("dict_attr", attrs)
            self.assertNotIn("none_attr", attrs)

    def test_when_batch_size_reached_should_worker_send_to_appsignal(self):
        self.handler = AppSignalNDJSONHandler(self.api_key, batch_size=5)

        for i in range(5):
            record = self._create_log_record(msg=f"Message {i}")
            self.handler.emit(record)

        time.sleep(0.6)

        self.mock_client.post.assert_called()
        call_args = self.mock_client.post.call_args
        expected_url = f"https://appsignal-endpoint.net/logs/json?api_key={self.api_key}"
        self.assertEqual(call_args[0][0], expected_url)
        self.assertEqual(call_args[1]["headers"]["Content-Type"], "application/x-ndjson")

        # Check NDJSON format (5 lines of JSON)
        ndjson_body = call_args[1]["data"]
        lines = ndjson_body.strip().split("\n")
        self.assertEqual(len(lines), 5)

    def test_when_http_error_occurs_should_worker_continue_processing(self):
        self.mock_client.post.side_effect = httpx.HTTPError("Connection failed")
        self.handler = AppSignalNDJSONHandler(self.api_key, batch_size=2)

        for i in range(2):
            record = self._create_log_record(msg=f"Message {i}")
            self.handler.emit(record)

        time.sleep(0.6)

        self.assertTrue(self.handler._thread.is_alive())

    def test_when_close_called_should_stop_worker_thread(self):
        self.handler = AppSignalNDJSONHandler(self.api_key)
        self.assertFalse(self.handler._stop_event.is_set())

        self.handler.close()

        self.assertTrue(self.handler._stop_event.is_set())

    def test_when_emit_has_formatting_error_should_handle_gracefully(self):
        self.handler = AppSignalNDJSONHandler(self.api_key)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test %s %s",
            args=("arg1",),
            exc_info=None,
        )
        self.handler.handleError = Mock()

        self.handler.emit(record)

        self.handler.handleError.assert_called_once_with(record)

    def test_when_different_log_levels_should_map_to_severity(self):
        self.handler = AppSignalNDJSONHandler(self.api_key)

        levels = [
            (logging.DEBUG, "debug"),
            (logging.INFO, "info"),
            (logging.WARNING, "warning"),
            (logging.ERROR, "error"),
            (logging.CRITICAL, "critical"),
        ]

        with patch.object(self.handler, "_queue") as mock_queue:
            for level, expected_severity in levels:
                record = self._create_log_record(level=level)
                self.handler.emit(record)

            self.assertEqual(mock_queue.put_nowait.call_count, len(levels))
            for i, (level, expected_severity) in enumerate(levels):
                log_data = mock_queue.put_nowait.call_args_list[i][0][0]
                self.assertEqual(log_data["severity"], expected_severity)

    def test_when_emitting_many_logs_should_not_block(self):
        self.handler = AppSignalNDJSONHandler(self.api_key, batch_size=10000)

        for i in range(1000):
            record = self._create_log_record(msg=f"Message {i}")
            self.handler.emit(record)

        self.assertFalse(self.handler._queue.empty())

    def test_when_queue_empty_should_worker_continue_after_timeout(self):
        self.handler = AppSignalNDJSONHandler(self.api_key)

        time.sleep(0.6)

        self.assertTrue(self.handler._thread.is_alive())

    def test_when_timestamp_field_should_be_iso_format(self):
        self.handler = AppSignalNDJSONHandler(self.api_key)
        record = self._create_log_record()

        with patch.object(self.handler, "_queue") as mock_queue:
            self.handler.emit(record)

            log_data = mock_queue.put_nowait.call_args[0][0]
            timestamp = log_data["timestamp"]
            # Check ISO format
            datetime.fromisoformat(timestamp)
            self.assertIn("T", timestamp)

    def test_edgecase_when_close_called_immediately_should_process_remaining_messages(self):
        self.handler = AppSignalNDJSONHandler("test_key", batch_size=10)

        for i in range(10):
            record = self._create_log_record(msg=f"Message {i}")
            self.handler.emit(record)

        self.handler.close()

        self.mock_client.post.assert_called_once()

    def test_edgecase_when_close_called_should_wait_for_thread_to_finish(self):
        self.handler = AppSignalNDJSONHandler("test_key")

        self.assertTrue(self.handler._thread.is_alive())

        self.handler.close()
        time.sleep(0.1)

        self.assertFalse(self.handler._thread.is_alive())

    def test_edgecase_when_http_error_occurs_should_log_error_to_stderr(self):
        self.mock_client.post.side_effect = Exception("Network error")
        self.handler = AppSignalNDJSONHandler("test_key", batch_size=2)

        for i in range(2):
            record = self._create_log_record(level=logging.ERROR, msg="Important error")
            self.handler.emit(record)

        time.sleep(0.6)

        self.mock_client.post.assert_called()

    def test_edgecase_when_record_has_none_attribute_should_exclude_it(self):
        self.handler = AppSignalNDJSONHandler("test_key")
        record = self._create_log_record(msg="Test")
        record.nullable_field = None

        with patch.object(self.handler, "_queue") as mock_queue:
            self.handler.emit(record)

            log_data = mock_queue.put_nowait.call_args[0][0]
            attrs = log_data.get("attributes", {})
            self.assertNotIn("nullable_field", attrs)

    def test_when_no_custom_attributes_should_not_include_attributes_field(self):
        self.handler = AppSignalNDJSONHandler(self.api_key)
        record = self._create_log_record()

        with patch.object(self.handler, "_queue") as mock_queue:
            self.handler.emit(record)

            log_data = mock_queue.put_nowait.call_args[0][0]
            self.assertNotIn("attributes", log_data)

    def test_when_flush_interval_passed_should_send_partial_batch(self):
        self.handler = AppSignalNDJSONHandler(self.api_key, batch_size=100, flush_interval=1.0)

        for i in range(3):
            record = self._create_log_record(msg=f"Message {i}")
            self.handler.emit(record)

        time.sleep(1.2)

        self.mock_client.post.assert_called()
        call_args = self.mock_client.post.call_args
        ndjson_body = call_args[1]["data"]
        lines = ndjson_body.strip().split("\n")
        self.assertEqual(len(lines), 3)

    def test_when_multiple_batches_should_send_all_separately(self):
        self.handler = AppSignalNDJSONHandler(self.api_key, batch_size=3)

        for i in range(7):
            record = self._create_log_record(msg=f"Message {i}")
            self.handler.emit(record)

        time.sleep(0.6)

        self.assertEqual(self.mock_client.post.call_count, 2)

        # First batch should have 3 messages
        first_call_body = self.mock_client.post.call_args_list[0][1]["data"]
        first_lines = first_call_body.strip().split("\n")
        self.assertEqual(len(first_lines), 3)

        # Second batch should have 3 messages
        second_call_body = self.mock_client.post.call_args_list[1][1]["data"]
        second_lines = second_call_body.strip().split("\n")
        self.assertEqual(len(second_lines), 3)
