"""
Database Snapshot Manager.
Ensures zero-touch read-only operation over production timetracker / afterimage databases.
"""

import os
import shutil
import sqlite3
import tempfile
from pathlib import Path
from typing import Optional


class SnapshotDBManager:
    """
    Safely creates and manages an isolated temporary snapshot of the production database.
    Guarantees no modifications or writes touch the original database.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.original_path = self._resolve_db_path(db_path)
        self.snapshot_path: Optional[str] = None
        self._temp_dir: Optional[tempfile.TemporaryDirectory] = None

    def _resolve_db_path(self, explicit_path: Optional[str]) -> Optional[Path]:
        if explicit_path:
            p = Path(explicit_path).expanduser().resolve()
            if p.exists():
                return p
            return None

        # Check Afterimage local db first, fallback to desktop-timetracker
        candidates = [
            Path("~/.local/share/afterimage/afterimage.db").expanduser(),
            Path("~/.local/share/timetracker/timetracker.db").expanduser(),
        ]
        for c in candidates:
            if c.exists():
                return c.resolve()
        return None

    def create_snapshot(self) -> str:
        """
        Copies the target DB into a temporary snapshot file and marks the connection as read-only.
        Returns the snapshot path.
        """
        if not self.original_path or not self.original_path.exists():
            raise FileNotFoundError("Production database not found for snapshot.")

        self._temp_dir = tempfile.TemporaryDirectory(prefix="afterimage_snapshot_")
        snapshot_file = Path(self._temp_dir.name) / "snapshot.db"
        shutil.copy2(self.original_path, snapshot_file)
        
        # Verify copied file is accessible
        self.snapshot_path = str(snapshot_file)
        return self.snapshot_path

    def get_connection(self) -> sqlite3.Connection:
        """
        Returns a read-only SQLite connection to the snapshot.
        """
        if not self.snapshot_path:
            self.create_snapshot()
            
        uri = f"file:{self.snapshot_path}?mode=ro"
        con = sqlite3.connect(uri, uri=True)
        con.row_factory = sqlite3.Row
        return con

    def cleanup(self):
        """Removes the temporary snapshot directory."""
        if self._temp_dir:
            try:
                self._temp_dir.cleanup()
            except Exception:
                pass
            self._temp_dir = None
            self.snapshot_path = None

    def __enter__(self):
        self.create_snapshot()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
