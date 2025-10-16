"""
Log rotation implementation.

Provides automatic log rotation based on:
- File size (100MB default)
- Time (midnight UTC)
- Compression of rotated files (gzip)
- Retention policy (30 days default)
"""

from __future__ import annotations

import gzip
import os
import shutil
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

import orjson

from ..models.log_config import LogConfig

__all__ = ["RotatingLogHandler"]


class RotatingLogHandler:
    """
    Handler for automatic log file rotation.
    
    Features:
    - Size-based rotation (default 100MB)
    - Time-based rotation (midnight UTC)
    - Gzip compression of rotated files
    - Retention policy (default 30 days)
    - Thread-safe operations
    """
    
    def __init__(self, config: LogConfig) -> None:
        """
        Initialize the rotating log handler.
        
        Args:
            config: LogConfig with rotation settings
        """
        self.config = config
        self.base_path = Path(config.output_file)
        self.max_bytes = config.rotation_max_bytes
        self.retention_days = config.retention_days
        self.compression_enabled = config.compression_enabled
        
        # Thread safety
        self._lock = threading.Lock()
        self._file = None
        self._current_date = None
        self._current_size = 0
        
        # Ensure directory exists
        self.base_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Open initial file
        self._open_file()
        
        # Cleanup old files
        self.cleanup_old_files()
    
    def write_log(self, entry: Dict[str, Any]) -> None:
        """
        Write a log entry, rotating if necessary.
        
        Args:
            entry: Log entry dictionary
        """
        with self._lock:
            # Check if rotation is needed
            if self._should_rotate():
                self._rotate()
            
            # Serialize and write
            try:
                json_bytes = orjson.dumps(entry)
                self._file.write(json_bytes)
                self._file.write(b"\n")
                self._file.flush()
                
                # Update size tracking
                self._current_size += len(json_bytes) + 1
                
            except Exception as e:
                # Log write error to stderr but don't crash
                import sys
                sys.stderr.write(f"ERROR: Failed to write log: {e}\n")
    
    def _should_rotate(self) -> bool:
        """Check if rotation is needed based on size or date."""
        # Check size limit
        if self._current_size >= self.max_bytes:
            return True
        
        # Check date change (midnight rotation)
        today = datetime.utcnow().date()
        if self._current_date is None:
            self._current_date = today
            return False
        
        if today > self._current_date:
            return True
        
        return False
    
    def _rotate(self) -> None:
        """Perform log rotation."""
        # Close current file
        if self._file:
            self._file.close()
        
        # Generate rotated filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y-%m-%d-%H%M%S")
        rotated_name = f"{self.base_path.stem}-{timestamp}{self.base_path.suffix}"
        rotated_path = self.base_path.parent / rotated_name
        
        # Rename current file to rotated name
        if self.base_path.exists():
            try:
                self.base_path.rename(rotated_path)
                
                # Compress if enabled
                if self.compression_enabled:
                    self._compress_file(rotated_path)
                    
            except Exception as e:
                import sys
                sys.stderr.write(f"ERROR: Failed to rotate log file: {e}\n")
        
        # Open new file
        self._open_file()
        
        # Cleanup old files
        self.cleanup_old_files()
    
    def _compress_file(self, file_path: Path) -> None:
        """
        Compress a log file with gzip.
        
        Args:
            file_path: Path to file to compress
        """
        gz_path = Path(str(file_path) + ".gz")
        
        try:
            with open(file_path, "rb") as f_in:
                with gzip.open(gz_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove original file after successful compression
            file_path.unlink()
            
        except Exception as e:
            import sys
            sys.stderr.write(f"ERROR: Failed to compress log file {file_path}: {e}\n")
    
    def _open_file(self) -> None:
        """Open a new log file."""
        try:
            self._file = open(self.base_path, "ab")
            self._current_date = datetime.utcnow().date()
            
            # Get current file size
            try:
                self._current_size = self.base_path.stat().st_size
            except FileNotFoundError:
                self._current_size = 0
                
        except Exception as e:
            import sys
            sys.stderr.write(f"ERROR: Failed to open log file {self.base_path}: {e}\n")
            # Create a dummy file object that ignores writes
            import io
            self._file = io.BytesIO()
    
    def cleanup_old_files(self) -> None:
        """Delete log files older than retention_days."""
        if self.retention_days <= 0:
            return
        
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        
        # Find all log files in directory
        log_dir = self.base_path.parent
        pattern = f"{self.base_path.stem}-*{self.base_path.suffix}*"
        
        for log_file in log_dir.glob(pattern):
            try:
                # Skip the active file
                if log_file == self.base_path:
                    continue
                
                # Check file modification time
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                
                if mtime < cutoff_date:
                    log_file.unlink()
                    
            except Exception as e:
                import sys
                sys.stderr.write(f"ERROR: Failed to delete old log file {log_file}: {e}\n")
    
    def flush(self) -> None:
        """Flush buffered data to disk."""
        with self._lock:
            if self._file:
                try:
                    self._file.flush()
                    os.fsync(self._file.fileno())
                except Exception:
                    pass
    
    def close(self) -> None:
        """Close the handler and release resources."""
        with self._lock:
            if self._file:
                try:
                    self._file.flush()
                    self._file.close()
                except Exception:
                    pass
                finally:
                    self._file = None
    
    def __del__(self) -> None:
        """Cleanup on deletion."""
        self.close()
