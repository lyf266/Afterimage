#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cognitive Analyzer for Afterimage
Coordinates session grouping, context-switching metrics calculation,
privacy sanitization, and AI retrospective generation.
"""

from typing import Any, Dict, List, Optional
from .client import BaseAIClient
from .prompts import PromptCatalog
from .sanitizer import PrivacySanitizer


class CognitiveAnalyzer:
    def __init__(self, ai_client: BaseAIClient, sanitizer: Optional[PrivacySanitizer] = None):
        self.client = ai_client
        self.sanitizer = sanitizer or PrivacySanitizer()

    def generate_daily_retrospective(self, date_str: str, summary_data: Dict[str, Any]) -> str:
        """
        Takes raw telemetry summary metrics for a date, scrubs sensitive tokens,
        and prompts the AI model to generate an executive cognitive retrospective.
        """
        # Format metrics
        total_duration = summary_data.get("total_duration", "0m")
        active_duration = summary_data.get("active_duration", "0m")
        switch_count = summary_data.get("switch_count", 0)
        total_keystrokes = summary_data.get("total_keystrokes", 0)
        avg_kpm = summary_data.get("avg_kpm", 0.0)
        mouse_distance = summary_data.get("mouse_distance", "0 m")

        # Category breakdown
        cat_lines = []
        for cat, dur, pct in summary_data.get("categories", []):
            cat_lines.append(f"- **{cat}**: {dur} ({pct:.1f}%)")
        category_breakdown = "\n".join(cat_lines) if cat_lines else "None recorded."

        # Top applications (sanitized)
        app_lines = []
        for app_name, dur, pct in summary_data.get("top_apps", []):
            clean_app = self.sanitizer.sanitize(app_name)
            app_lines.append(f"- {clean_app}: {dur} ({pct:.1f}%)")
        top_applications = "\n".join(app_lines) if app_lines else "None recorded."

        # Fragile windows (periods with high switch rate)
        fragile_lines = []
        for hour, switches in summary_data.get("high_switch_hours", []):
            fragile_lines.append(f"- Hour {hour:02d}:00: {switches} window focus switches")
        fragile_windows = "\n".join(fragile_lines) if fragile_lines else "Stable focus throughout."

        prompt = PromptCatalog.DAILY_RETROSPECTIVE_USER.format(
            date=date_str,
            total_duration=total_duration,
            active_duration=active_duration,
            switch_count=switch_count,
            total_keystrokes=total_keystrokes,
            avg_kpm=f"{avg_kpm:.1f}",
            mouse_distance=mouse_distance,
            category_breakdown=category_breakdown,
            top_applications=top_applications,
            fragile_windows=fragile_windows,
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

        context_data = "\n".join(context_lines) if context_lines else "No activity matching criteria."
        user_prompt = PromptCatalog.NATURAL_LANGUAGE_QUERY.format(
            context_data=context_data,
            user_query=user_query,
        )

        return self.client.generate(
            system_prompt=PromptCatalog.SYSTEM_COGNITIVE_ANALYST,
            user_prompt=user_prompt,
        )
