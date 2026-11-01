import unittest
from datetime import datetime, timedelta

from src.ai.clustering import SessionClusterer, WorkSession


class TestSessionClustering(unittest.TestCase):
    def setUp(self):
        self.clusterer = SessionClusterer(idle_split_seconds=120.0)

    def test_clustering_continuous_activities(self):
        t0 = datetime(2026, 10, 31, 10, 0, 0)
        raw = [
            {
                "start_time": (t0 + timedelta(seconds=i * 5)).strftime("%Y-%m-%d %H:%M:%S"),
                "end_time": (t0 + timedelta(seconds=(i + 1) * 5)).strftime("%Y-%m-%d %H:%M:%S"),
                "duration_seconds": 5,
                "app_name": "Ghostty",
                "window_title": "nvim src/main.py",
                "category": "development",
                "is_idle": 0,
                "is_locked": 0,
                "key_presses": 15,
                "mouse_clicks": 2,
                "mouse_distance_px": 100.0,
            }
            for i in range(12)  # 60 seconds total
        ]

        sessions = self.clusterer.cluster(raw)
        self.assertEqual(len(sessions), 1)
        sess = sessions[0]
        self.assertEqual(sess.primary_app, "Ghostty")
        self.assertEqual(sess.duration_seconds, 60.0)
        self.assertEqual(sess.key_presses, 180)
        self.assertEqual(sess.kpm, 180.0)

    def test_clustering_split_on_lock_or_long_idle(self):
        t0 = datetime(2026, 10, 31, 10, 0, 0)
        raw = [
            {
                "start_time": "2026-10-31 10:00:00",
                "end_time": "2026-10-31 10:05:00",
                "duration_seconds": 300,
                "app_name": "Ghostty",
                "window_title": "dev",
                "category": "development",
                "is_idle": 0,
                "is_locked": 0,
                "key_presses": 200,
                "mouse_clicks": 20,
                "mouse_distance_px": 500.0,
            },
            {
                "start_time": "2026-10-31 10:05:00",
                "end_time": "2026-10-31 10:15:00",
                "duration_seconds": 600,
                "app_name": "屏幕已锁定",
                "window_title": "屏幕已锁定",
                "category": "locked",
                "is_idle": 0,
                "is_locked": 1,
                "key_presses": 0,
                "mouse_clicks": 0,
                "mouse_distance_px": 0.0,
            },
            {
                "start_time": "2026-10-31 10:15:00",
                "end_time": "2026-10-31 10:35:00",
                "duration_seconds": 1200,
                "app_name": "Orca",
                "window_title": "planning",
                "category": "development",
                "is_idle": 0,
                "is_locked": 0,
                "key_presses": 800,
                "mouse_clicks": 40,
                "mouse_distance_px": 1200.0,
            },
        ]

        sessions = self.clusterer.cluster(raw)
        self.assertEqual(len(sessions), 3)
        metrics = self.clusterer.calculate_flow_metrics(sessions)

        self.assertEqual(metrics.total_duration_seconds, 2100.0)
        self.assertEqual(metrics.locked_duration_seconds, 600.0)
        self.assertEqual(metrics.active_duration_seconds, 1500.0)
        self.assertIsNotNone(metrics.longest_flow_session)
        self.assertEqual(metrics.longest_flow_session.primary_app, "Orca")
        self.assertEqual(metrics.flow_streak_minutes, 20.0)


if __name__ == "__main__":
    unittest.main()
