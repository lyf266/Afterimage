"""
Session Clustering and Cognitive Flow Metrics Engine.
Aggregates discrete 5-second window activities into continuous work sessions,
and calculates flow state duration, attention fragmentation index, and cognitive switches.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class ActivityRecord:
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    app_name: str
    window_title: str
    category: str
    is_idle: bool
    is_locked: bool
    key_presses: int
    mouse_clicks: int
    mouse_distance_px: float
    focus_level: int
    focus_score: float


@dataclass
class WorkSession:
    start_time: datetime
    end_time: datetime
    primary_app: str
    category: str
    summary_title: str
    duration_seconds: float = 0.0
    active_seconds: float = 0.0
    idle_seconds: float = 0.0
    key_presses: int = 0
    mouse_clicks: int = 0
    mouse_distance_px: float = 0.0
    context_switches: int = 0
    sub_activities: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def duration_minutes(self) -> float:
        return round(self.duration_seconds / 60.0, 1)

    @property
    def kpm(self) -> float:
        mins = self.active_seconds / 60.0
        return round(self.key_presses / mins, 1) if mins > 0 else 0.0


@dataclass
class FlowMetrics:
    total_duration_seconds: float
    active_duration_seconds: float
    idle_duration_seconds: float
    locked_duration_seconds: float
    deep_work_seconds: float
    longest_flow_session: Optional[WorkSession]
    flow_streak_minutes: float
    fragmentation_count: int
    cognitive_switches: int
    energy_efficiency_pct: int
    output_energy_ratio: float
    total_keys: int
    total_clicks: int
    total_mouse_meters: float
    sessions: List[WorkSession]


class SessionClusterer:
    """
    Groups atomic window heartbeats into continuous work sessions based on
    semantic similarity, category continuity, and idle/lock boundaries.
    """

    def __init__(self, idle_split_seconds: float = 180.0, switch_split_seconds: float = 300.0):
        self.idle_split_seconds = idle_split_seconds
        self.switch_split_seconds = switch_split_seconds

    def cluster(self, raw_records: List[Dict[str, Any]]) -> List[WorkSession]:
        if not raw_records:
            return []

        # Parse & sort chronologically
        records: List[ActivityRecord] = []
        for r in raw_records:
            s_dt = self._parse_dt(r.get("start_time"))
            e_dt = self._parse_dt(r.get("end_time"))
            if not s_dt or not e_dt:
                continue
            dur = float(r.get("duration_seconds", (e_dt - s_dt).total_seconds()))
            records.append(
                ActivityRecord(
                    start_time=s_dt,
                    end_time=e_dt,
                    duration_seconds=dur,
                    app_name=r.get("app_name") or "Unknown",
                    window_title=r.get("window_title") or "",
                    category=r.get("category") or "general",
                    is_idle=bool(r.get("is_idle", 0)),
                    is_locked=bool(r.get("is_locked", 0) or r.get("app_name") == "屏幕已锁定"),
                    key_presses=int(r.get("key_presses", 0)),
                    mouse_clicks=int(r.get("mouse_clicks", 0)),
                    mouse_distance_px=float(r.get("mouse_distance_px", 0.0)),
                    focus_level=int(r.get("focus_level", 0)),
                    focus_score=float(r.get("focus_score", 0.0)),
                )
            )

        records.sort(key=lambda x: x.start_time)
        if not records:
            return []

        sessions: List[WorkSession] = []
        current_sess: Optional[WorkSession] = None

        for rec in records:
            if current_sess is None:
                current_sess = self._create_new_session(rec)
                continue

            time_gap = (rec.start_time - current_sess.end_time).total_seconds()
            is_locked = rec.is_locked or current_sess.category == "locked"
            
            # Boundary conditions to break session:
            # 1. Lock screen transition
            # 2. Large idle gap (> idle_split_seconds)
            # 3. Completely different category or app after significant duration
            should_break = False
            if rec.is_locked != (current_sess.category == "locked"):
                should_break = True
            elif time_gap > self.idle_split_seconds:
                should_break = True
            elif (
                rec.app_name != current_sess.primary_app
                and rec.category != current_sess.category
                and time_gap > 30.0
            ):
                should_break = True

            if should_break:
                sessions.append(current_sess)
                current_sess = self._create_new_session(rec)
            else:
                self._merge_into_session(current_sess, rec)

        if current_sess:
            sessions.append(current_sess)

        return sessions

    def calculate_flow_metrics(self, sessions: List[WorkSession]) -> FlowMetrics:
        total_dur = sum(s.duration_seconds for s in sessions)
        active_dur = sum(s.active_seconds for s in sessions if s.category != "locked")
        idle_dur = sum(s.idle_seconds for s in sessions)
        locked_dur = sum(s.duration_seconds for s in sessions if s.category == "locked")

        total_keys = sum(s.key_presses for s in sessions)
        total_clicks = sum(s.mouse_clicks for s in sessions)
        total_px = sum(s.mouse_distance_px for s in sessions)
        total_meters = round(total_px * 0.0254 / 96.0, 1)

        # Deep work sessions: duration >= 15 mins (900s), active and category in focus domains
        deep_sessions = [
            s for s in sessions 
            if s.category not in ("locked", "idle", "entertainment", "social")
            and s.duration_seconds >= 900
        ]
        deep_work_seconds = sum(s.active_seconds for s in deep_sessions)

        # Longest continuous flow session (non-locked, high active proportion)
        valid_flow = [s for s in sessions if s.category != "locked" and s.active_seconds >= 300]
        longest_flow = max(valid_flow, key=lambda s: s.duration_seconds) if valid_flow else None
        longest_minutes = longest_flow.duration_minutes if longest_flow else 0.0

        # Fragmentation count: sessions under 3 minutes that caused a switch away
        frag_sessions = [
            s for s in sessions 
            if s.category != "locked" and s.duration_seconds < 180 and s.context_switches > 0
        ]
        frag_count = len(frag_sessions)
        total_switches = sum(s.context_switches for s in sessions)

        # Energy efficiency: ratio of active deep work to total work
        work_dur = total_dur - locked_dur
        energy_eff = int(min(100, max(10, (active_dur / work_dur * 100)))) if work_dur > 0 else 0
        output_energy_ratio = round(min(1.0, (active_dur / max(1.0, total_dur))), 2)

        return FlowMetrics(
            total_duration_seconds=total_dur,
            active_duration_seconds=active_dur,
            idle_duration_seconds=idle_dur,
            locked_duration_seconds=locked_dur,
            deep_work_seconds=deep_work_seconds,
            longest_flow_session=longest_flow,
            flow_streak_minutes=longest_minutes,
            fragmentation_count=frag_count,
            cognitive_switches=total_switches,
            energy_efficiency_pct=energy_eff,
            output_energy_ratio=output_energy_ratio,
            total_keys=total_keys,
            total_clicks=total_clicks,
            total_mouse_meters=total_meters,
            sessions=sessions,
        )

    def _create_new_session(self, rec: ActivityRecord) -> WorkSession:
        return WorkSession(
            start_time=rec.start_time,
            end_time=rec.end_time,
            primary_app=rec.app_name,
            category=rec.category if not rec.is_locked else "locked",
            summary_title=rec.window_title[:60] if rec.window_title else rec.app_name,
            duration_seconds=rec.duration_seconds,
            active_seconds=0.0 if rec.is_idle or rec.is_locked else rec.duration_seconds,
            idle_seconds=rec.duration_seconds if rec.is_idle else 0.0,
            key_presses=rec.key_presses,
            mouse_clicks=rec.mouse_clicks,
            mouse_distance_px=rec.mouse_distance_px,
            context_switches=0,
            sub_activities=[
                {
                    "app": rec.app_name,
                    "title": rec.window_title,
                    "dur": rec.duration_seconds,
                }
            ],
        )

    def _merge_into_session(self, sess: WorkSession, rec: ActivityRecord):
        sess.end_time = max(sess.end_time, rec.end_time)
        sess.duration_seconds += rec.duration_seconds
        if rec.is_idle:
            sess.idle_seconds += rec.duration_seconds
        elif not rec.is_locked:
            sess.active_seconds += rec.duration_seconds

        sess.key_presses += rec.key_presses
        sess.mouse_clicks += rec.mouse_clicks
        sess.mouse_distance_px += rec.mouse_distance_px

        if rec.app_name != sess.primary_app:
            sess.context_switches += 1

        sess.sub_activities.append(
            {
                "app": rec.app_name,
                "title": rec.window_title,
                "dur": rec.duration_seconds,
            }
        )

    @staticmethod
    def _parse_dt(dt_str: Any) -> Optional[datetime]:
        if isinstance(dt_str, datetime):
            return dt_str
        if not dt_str:
            return None
        dt_str = str(dt_str).strip()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"):
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue
        return None
