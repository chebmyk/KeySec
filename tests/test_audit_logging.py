"""Tests for KeySec audit logging."""

from __future__ import annotations

import json
import logging
import tempfile
import time
import unittest
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from keysec.audit import create_audit_logger
from keysec.model.keysec_config import AuditLoggingConfig


class AuditLoggerTests(unittest.TestCase):
    def test_disabled_audit_logging_does_not_create_a_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "audit.log"

            audit_logger = create_audit_logger(
                AuditLoggingConfig(enabled=False, file=str(log_path))
            )

            self.assertIsNone(audit_logger)
            self.assertFalse(log_path.exists())

    def test_unavailable_destination_does_not_change_operation_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "missing" / "audit.log"
            audit_logger = create_audit_logger(
                AuditLoggingConfig(enabled=True, file=str(log_path))
            )
            self.assertIsNotNone(audit_logger)
            assert audit_logger is not None
            self.addCleanup(audit_logger.close)

            def operation() -> str:
                return "operation result"

            with self.assertLogs("keysec.audit.errors", level="ERROR") as captured:
                result = audit_logger.run(
                    "secret_retrieval",
                    "vault",
                    operation,
                )

            self.assertEqual(result, "operation result")
            self.assertEqual(
                captured.output,
                ["ERROR:keysec.audit.errors:Audit log write failed"],
            )
            self.assertFalse(log_path.exists())

    def test_writes_only_audit_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "audit.log"
            audit_logger = create_audit_logger(
                AuditLoggingConfig(enabled=True, file=str(log_path))
            )
            self.assertIsNotNone(audit_logger)
            assert audit_logger is not None
            self.addCleanup(audit_logger.close)
            root_handlers = logging.getLogger().handlers.copy()

            audit_logger.record("decrypt", "local", succeeded=True)

            self.assertEqual(logging.getLogger().handlers, root_handlers)
            entry = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(
                set(entry),
                {"timestamp", "operation", "provider", "outcome"},
            )
            self.assertEqual(entry["operation"], "decrypt")
            self.assertEqual(entry["provider"], "local")
            self.assertEqual(entry["outcome"], "success")
            self.assertTrue(entry["timestamp"].endswith("+00:00"))

    def test_daily_rotation_preserves_prior_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "audit.log"
            audit_logger = create_audit_logger(
                AuditLoggingConfig(enabled=True, file=str(log_path))
            )
            self.assertIsNotNone(audit_logger)
            assert audit_logger is not None
            self.addCleanup(audit_logger.close)
            audit_logger.record("encrypt", "local", succeeded=True)

            handler = audit_logger._logger.handlers[0]
            self.assertIsInstance(handler, TimedRotatingFileHandler)
            self.assertEqual(handler.when, "MIDNIGHT")
            self.assertEqual(handler.interval, 86_400)
            handler.rolloverAt = int(time.time()) - 1

            audit_logger.record("decrypt", "local", succeeded=True)

            rotated_files = list(Path(temp_dir).glob("audit.log.*"))
            self.assertEqual(len(rotated_files), 1)
            self.assertEqual(
                json.loads(rotated_files[0].read_text(encoding="utf-8"))["operation"],
                "encrypt",
            )
            self.assertEqual(
                json.loads(log_path.read_text(encoding="utf-8"))["operation"],
                "decrypt",
            )

    def test_failed_operation_preserves_exception_and_excludes_exception_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "audit.log"
            audit_logger = create_audit_logger(
                AuditLoggingConfig(enabled=True, file=str(log_path))
            )
            self.assertIsNotNone(audit_logger)
            assert audit_logger is not None
            self.addCleanup(audit_logger.close)

            def operation() -> str:
                raise RuntimeError("sensitive exception detail")

            with self.assertRaisesRegex(RuntimeError, "sensitive exception detail"):
                audit_logger.run("secret_retrieval", "vault", operation)

            contents = log_path.read_text(encoding="utf-8")
            self.assertNotIn("sensitive exception detail", contents)
            entry = json.loads(contents.strip())
            self.assertEqual(entry["outcome"], "failure")
            self.assertEqual(entry["operation"], "secret_retrieval")


if __name__ == "__main__":
    unittest.main()
