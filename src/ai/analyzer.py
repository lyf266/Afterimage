#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cognitive Analyzer for Afterimage.
Coordinates session grouping, context-switching metrics calculation,
privacy sanitization, and AI retrospective generation.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from .client import BaseAIClient
from .prompts import PromptCatalog
from .sanitizer import PrivacySanitizer
from .clustering import FlowMetrics, WorkSession, SessionClusterer


class CognitiveAnalyzer:
    def __init__(self, ai_client: BaseAIClient, sanitizer: Optional[PrivacySanitizer] = None):
        self.client = ai_client
        self.sanitizer = sanitizer or PrivacySanitizer()
        self.clusterer = SessionClusterer()

    def generate_retrospective_from_metrics(
        self,
        metrics: FlowMetrics,
        period_str: str = "今日",
    ) -> str:
        """
        Uses FlowMetrics and WorkSessions to construct a structured prompt for the AI model.
        """
        total_hours = metrics.total_duration_seconds / 3600.0
        total_mins = metrics.total_duration_seconds / 60.0
        active_hours = metrics.active_duration_seconds / 3600.0
        active_mins = metrics.active_duration_seconds / 60.0
        locked_mins = metrics.locked_duration_seconds / 60.0
        active_ratio = (active_mins / total_mins * 100.0) if total_mins > 0 else 0.0

        deep_work_hours = metrics.deep_work_seconds / 3600.0
        deep_work_str = f"{deep_work_hours:.1f} 小时 ({metrics.deep_work_seconds/60.0:.0f} 分钟)"

        if metrics.longest_flow_session:
            s = metrics.longest_flow_session
            longest_str = (
                f"{metrics.flow_streak_minutes:.0f} 分钟 "
                f"({s.start_time.strftime('%H:%M')} ~ {s.end_time.strftime('%H:%M')}, {s.primary_app})"
            )
        else:
            longest_str = "无显著连续区间 (<5 分钟)"

        frag_summary = "极低" if metrics.fragmentation_count <= 2 else ("较低" if metrics.fragmentation_count <= 6 else "较高")

        # Format sessions (sanitized)
        session_lines = []
        for i, sess in enumerate(metrics.sessions[:15], 1):
            if sess.category == "locked":
                session_lines.append(
                    f"{i}. [锁屏挂起] {sess.start_time.strftime('%H:%M')}~{sess.end_time.strftime('%H:%M')} "
                    f"({sess.duration_minutes:.0f}m)"
                )
                continue

            app = self.sanitizer.sanitize(sess.primary_app)
            title = self.sanitizer.sanitize(sess.summary_title)
            session_lines.append(
                f"{i}. [{app}] {sess.start_time.strftime('%H:%M')}~{sess.end_time.strftime('%H:%M')} "
                f"({sess.duration_minutes:.0f}m, 按键: {sess.key_presses}, KPM: {sess.kpm:.0f}) - {title}"
            )
        session_summary = "\n".join(session_lines) if session_lines else "暂无聚合会话数据。"

        prompt = PromptCatalog.DAILY_RETROSPECTIVE_USER.format(
            period_str=period_str,
            total_duration_hours=total_hours,
            total_duration_mins=total_mins,
            active_hours=active_hours,
            active_mins=active_mins,
            active_ratio=active_ratio,
            locked_mins=locked_mins,
            total_keys=metrics.total_keys,
            total_clicks=metrics.total_clicks,
            total_meters=metrics.total_mouse_meters,
            longest_flow_str=longest_str,
            deep_work_str=deep_work_str,
            fragmentation_str=frag_summary,
            frag_count=metrics.fragmentation_count,
            energy_eff_pct=metrics.energy_efficiency_pct,
            output_energy_ratio=metrics.output_energy_ratio,
            session_summary=session_summary,
            deep_work_hours=deep_work_hours,
        )

        return self.client.generate(
            system_prompt=PromptCatalog.SYSTEM_COGNITIVE_ANALYST,
            user_prompt=prompt,
        )

    def answer_query(self, context_records: List[Dict[str, Any]], user_query: str) -> str:
        """
        Answer natural language questions about past activity based on sanitized telemetry records.
        """
        context_lines = []
        for rec in context_records:
            t_str = rec.get("time", "")
            app = self.sanitizer.sanitize(rec.get("app", ""))
            title = self.sanitizer.sanitize(rec.get("title", ""))
            dur = rec.get("duration", "")
            context_lines.append(f"[{t_str}] App: {app} | Duration: {dur} | Window: {title}")

        context_data = "\n".join(context_lines)
        prompt = PromptCatalog.NATURAL_LANGUAGE_QUERY.format(
            context_data=context_data,
            user_query=user_query,
        )

        return self.client.generate(
            system_prompt=PromptCatalog.SYSTEM_COGNITIVE_ANALYST,
            user_prompt=prompt,
        )
