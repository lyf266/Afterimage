import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.ai.clustering import FlowMetrics
from src.outputs.exporter import MultiChannelExporter


class TestMultiChannelExporter(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.daily_dir = Path(self.temp_dir.name) / "daily"
        self.obsidian_dir = Path(self.temp_dir.name) / "obsidian"
        self.exporter = MultiChannelExporter(
            daily_notes_dir=self.daily_dir,
            obsidian_dir=self.obsidian_dir,
            tg_bin=Path("/mock/bin/tg"),
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_export_daily_note_and_mirror(self):
        content = "## 📅 核心产出与重点事项\n1. 测试条目"
        p = self.exporter.export_daily_note("2026-10-31", content)
        self.assertTrue(p.exists())
        self.assertTrue((self.obsidian_dir / "2026-10-31.md").exists())
        text = p.read_text(encoding="utf-8")
        self.assertIn("每日总结 · 2026-10-31", text)
        self.assertIn("核心产出与重点事项", text)

    @patch("subprocess.run")
    def test_send_telegram_brief(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        metrics = FlowMetrics(
            total_duration_seconds=3600,
            active_duration_seconds=1800,
            idle_duration_seconds=600,
            locked_duration_seconds=1200,
            deep_work_seconds=1800,
            longest_flow_session=None,
            flow_streak_minutes=30.0,
            fragmentation_count=1,
            cognitive_switches=2,
            energy_efficiency_pct=80,
            output_energy_ratio=0.5,
            total_keys=1000,
            total_clicks=200,
            total_mouse_meters=30.0,
            sessions=[],
        )
        
        with patch.object(Path, "exists", return_value=True):
            res = self.exporter.send_telegram_brief("2026-10-31", metrics, "1. 完成开发")
            self.assertTrue(res)
            self.assertTrue(mock_run.called)


if __name__ == "__main__":
    unittest.main()
