"""
Custom logging handler that writes log messages to a local file.
This handler buffers log messages and writes them to a specified file path.
"""

import os
from datetime import datetime, timezone
import logging


class LocalLogHandler(logging.Handler):
    """
    Custom logging handler that writes log messages to a local file.
    This handler buffers log messages and writes them to a specified file path.
    """

    def __init__(self, base_dir: str = "../mnt/logs", prefix: str = "gbif_log"):
        super().__init__()
        os.makedirs(base_dir, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y_%m_%d_%H_%M_%S")
        self.log_path = os.path.join(base_dir, f"{prefix}_{timestamp}.log")

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record by formatting it and writing it to the log file.
        """
        log_entry = self.format(record)

        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
        except OSError as e:
            print("Error when writing log file %s: %s", self.log_path, e)
