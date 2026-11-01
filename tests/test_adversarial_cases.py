"""
Adversarial and Edge Case Verification Suite for Afterimage.
Covers:
1. Missing database handling and informative errors.
2. Mismatched / corrupt database schema.
3. Offline Ollama failure handling.
4. Cloud API request timeout / graceful error handling.
5. Custom sensitive word scrubbing and privacy sanitization limits.
6. Install/uninstall script safety (verifying no destruction of timetracker data).
"""

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.ai.client import GeminiClient, OllamaClient, OpenAICompatibleClient
from src.ai.sanitizer import PrivacySanitizer
from src.data.db_manager import SnapshotDBManager


class TestAdversarialEdgeCases(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_missing_database_raises_clear_error(self):
        non_existent = str(self.temp_path / "does_not_exist.db")
        manager = SnapshotDBManager(db_path=non_existent)
        with self.assertRaises(FileNotFoundError) as ctx:
            manager.create_snapshot()
        self.assertIn("数据库未找到", str(ctx.exception))

    def test_mismatched_schema_raises_clear_error(self):
        bad_db = self.temp_path / "corrupted.db"
        con = sqlite3.connect(bad_db)
        cur = con.cursor()
        cur.execute("CREATE TABLE wrong_table (id INT, note TEXT);")
        con.commit()
        con.close()

        manager = SnapshotDBManager(db_path=str(bad_db))
        with manager:
            with self.assertRaises(ValueError) as ctx:
                manager.get_connection()
            self.assertIn("数据库结构不匹配", str(ctx.exception))
            self.assertIn("window_activities", str(ctx.exception))

    def test_ollama_offline_raises_clear_actionable_error(self):
        # 127.0.0.1:54321 is an unused port where no Ollama is running
        client = OllamaClient(base_url="http://127.0.0.1:54321", model="qwen2.5:7b")
        with self.assertRaises(RuntimeError) as ctx:
            client.generate("system", "user")
        self.assertIn("本地 Ollama 服务未运行或无法连接", str(ctx.exception))
        self.assertIn("ollama serve", str(ctx.exception))

    @patch("urllib.request.OpenerDirector.open")
    def test_cloud_api_timeout_does_not_hang(self, mock_open):
        mock_open.side_effect = TimeoutError("Connection timed out")
        client = GeminiClient(api_key="test_key")
        with self.assertRaises(RuntimeError) as ctx:
            client.generate("system", "user")
        self.assertIn("超时", str(ctx.exception))

    def test_custom_sensitive_words_scrubbing(self):
        custom_words = ["TopSecretProject", "MyInternalSecretCode"]
        sanitizer = PrivacySanitizer(custom_words=custom_words)
        
        raw_text = "Working on TopSecretProject with MyInternalSecretCode in nvim"
        cleaned = sanitizer.sanitize(raw_text)
        
        self.assertNotIn("TopSecretProject", cleaned)
        self.assertNotIn("MyInternalSecretCode", cleaned)
        self.assertEqual(cleaned, "Working on [REDACTED] with [REDACTED] in nvim")

    def test_uninstall_script_never_touches_timetracker_data(self):
        uninstall_sh = (Path(__file__).resolve().parent.parent / "uninstall.sh").read_text(encoding="utf-8")
        # Ensure uninstall.sh never targets timetracker database
        self.assertNotIn("rm -rf ${HOME}/.local/share/timetracker", uninstall_sh)
        self.assertNotIn("rm -rf ~/.local/share/timetracker", uninstall_sh)
        self.assertNotIn("timetracker.db", uninstall_sh)


if __name__ == "__main__":
    unittest.main()
