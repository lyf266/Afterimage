import unittest
from datetime import datetime
from io import StringIO
from rich.console import Console

from src.ai.clustering import FlowMetrics, WorkSession
from src.ai.dashboard import TerminalDashboard


class TestTerminalDashboard(unittest.TestCase):
    def setUp(self):
        self.output = StringIO()
        self.console = Console(file=self.output, width=100, force_terminal=False)
        self.dashboard = TerminalDashboard(console=self.console)

    def test_render_cards_and_tables(self):
        t0 = datetime(2026, 10, 31, 10, 0, 0)
        t1 = datetime(2026, 10, 31, 10, 30, 0)
        s = WorkSession(
            start_time=t0,
            end_time=t1,
            primary_app="Orca",
            category="development",
            summary_title="Coding afterimage",
            duration_seconds=1800,
            active_seconds=1800,
            key_presses=500,
        )

        metrics = FlowMetrics(
            total_duration_seconds=3600,
            active_duration_seconds=1800,
            idle_duration_seconds=600,
            locked_duration_seconds=1200,
            deep_work_seconds=1800,
            longest_flow_session=s,
            flow_streak_minutes=30.0,
            fragmentation_count=1,
            cognitive_switches=3,
            energy_efficiency_pct=75,
            output_energy_ratio=0.5,
            total_keys=500,
            total_clicks=100,
            total_mouse_meters=50.0,
            sessions=[s],
        )

        self.dashboard.render_header()
        self.dashboard.render_metrics_cards(metrics)
        self.dashboard.render_sessions_table(metrics.sessions)
        self.dashboard.render_ai_retrospective("## Test Retrospective\nContent")

        rendered = self.output.getvalue()
        self.assertIn("Afterimage", rendered)
        self.assertIn("Orca", rendered)
        self.assertIn("30m", rendered)
        self.assertIn("Test Retrospective", rendered)

    def test_render_english_dashboard(self):
        output_en = StringIO()
        console_en = Console(file=output_en, width=100, force_terminal=False)
        dashboard_en = TerminalDashboard(console=console_en, lang="en")

        t0 = datetime(2026, 10, 31, 10, 0, 0)
        t1 = datetime(2026, 10, 31, 10, 30, 0)
        s = WorkSession(
            start_time=t0,
            end_time=t1,
            primary_app="Orca",
            category="development",
            summary_title="Coding afterimage",
            duration_seconds=1800,
            active_seconds=1800,
            key_presses=500,
        )

        metrics = FlowMetrics(
            total_duration_seconds=3600,
            active_duration_seconds=1800,
            idle_duration_seconds=600,
            locked_duration_seconds=1200,
            deep_work_seconds=1800,
            longest_flow_session=s,
            flow_streak_minutes=30.0,
            fragmentation_count=1,
            cognitive_switches=3,
            energy_efficiency_pct=75,
            output_energy_ratio=0.5,
            total_keys=500,
            total_clicks=100,
            total_mouse_meters=50.0,
            sessions=[s],
        )

        dashboard_en.render_metrics_cards(metrics)
        dashboard_en.render_sessions_table(metrics.sessions)
        dashboard_en.render_ai_retrospective("## Daily AI Synthesis\nClean retrospective")

        rendered = output_en.getvalue()
        self.assertIn("Active / Total Time", rendered)
        self.assertIn("Longest Focus Streak", rendered)
        self.assertIn("Energy Utilization", rendered)
        self.assertIn("Fragmentation Index", rendered)
        self.assertIn("Hardware Dynamics", rendered)
        self.assertIn("Work Sessions (Session Clusters)", rendered)
        self.assertIn("AI Cognitive Retrospective Report", rendered)


if __name__ == "__main__":
    unittest.main()
