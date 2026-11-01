import os
import unittest
import tempfile
import sqlite3
from pathlib import Path

from src.data.db_manager import SnapshotDBManager


class TestSnapshotDBManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.prod_db_path = Path(self.temp_dir.name) / "timetracker_mock.db"
        
        # Create a mock production DB
        con = sqlite3.connect(self.prod_db_path)
        cur = con.cursor()
        cur.execute("CREATE TABLE activities (id INTEGER PRIMARY KEY, app TEXT);")
        cur.execute("INSERT INTO activities (app) VALUES ('ghostty');")
        con.commit()
        con.close()
        
        self.original_mtime = self.prod_db_path.stat().st_mtime_ns

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_snapshot_creation_and_readonly(self):
        manager = SnapshotDBManager(db_path=str(self.prod_db_path))
        with manager:
            self.assertTrue(Path(manager.snapshot_path).exists())
            con = manager.get_connection()
            cur = con.cursor()
            rows = cur.execute("SELECT app FROM activities;").fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["app"], "ghostty")
            
            # Verify read-only restriction: attempting write should fail
            with self.assertRaises(sqlite3.OperationalError):
                cur.execute("INSERT INTO activities (app) VALUES ('malicious_write');")
            con.close()

        # Check original production file was never touched
        self.assertEqual(self.prod_db_path.stat().st_mtime_ns, self.original_mtime)
        # Snapshot path should be cleaned up
        self.assertIsNone(manager.snapshot_path)


if __name__ == "__main__":
    unittest.main()
