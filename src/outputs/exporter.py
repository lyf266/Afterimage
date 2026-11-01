#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Channel Exporter and Telegram Dispatcher for Afterimage.
Handles sync to:
1. Local Markdown Daily Notes: /home/f1are/文档/人生出路与战略抉择/每周复盘/每日总结/YYYY-MM-DD.md
2. Obsidian Vault: /home/f1are/obsidian-vault/人生出路与战略抉择/每周复盘/每日总结/YYYY-MM-DD.md
3. Telegram Push via native tg CLI
"""

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from ai.clustering import FlowMetrics


class MultiChannelExporter:
    """
    Exports daily cognitive retrospectives to Markdown daily notes, Obsidian vault, and Telegram.
    """

    DEFAULT_DAILY_DIR = Path("/home/f1are/文档/人生出路与战略抉择/每周复盘/每日总结")
    DEFAULT_OBSIDIAN_DIR = Path("/home/f1are/obsidian-vault/人生出路与战略抉择/每周复盘/每日总结")
    TG_BIN = Path("/home/f1are/.local/bin/tg")

    def __init__(
        self,
        daily_notes_dir: Optional[Path] = None,
        obsidian_dir: Optional[Path] = None,
        tg_bin: Optional[Path] = None,
    ):
        self.daily_notes_dir = (daily_notes_dir or self.DEFAULT_DAILY_DIR).expanduser()
        self.obsidian_dir = (obsidian_dir or self.DEFAULT_OBSIDIAN_DIR).expanduser()
        self.tg_bin = (tg_bin or self.TG_BIN).expanduser()

    def export_daily_note(
        self,
        date_str: str,
        retrospective_content: str,
        period_str: Optional[str] = None,
    ) -> Path:
        """
        Writes the daily summary markdown conforming to the user's template.
        """
        self.daily_notes_dir.mkdir(parents=True, exist_ok=True)
        note_path = self.daily_notes_dir / f"{date_str}.md"

        # Format header with tracking cycle
        cycle_desc = period_str or f"{date_str} 14:00 ~ 次日 14:00 (GMT-7)"
        header = f"# 每日总结 · {date_str}\n\n> **统计周期**：`{cycle_desc}`\n\n---\n\n"

        full_content = header + retrospective_content.strip() + "\n"

        with open(note_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        # Mirror to Obsidian vault if available
        try:
            self.obsidian_dir.mkdir(parents=True, exist_ok=True)
            obsidian_path = self.obsidian_dir / f"{date_str}.md"
            shutil.copy2(note_path, obsidian_path)
        except Exception:
            pass

        return note_path

    def send_telegram_brief(
        self,
        date_str: str,
        metrics: FlowMetrics,
        brief_summary: str,
    ) -> bool:
        """
        Sends formatted brief directly to Telegram via tg CLI.
        Format:
        📅
        1. ...
        2. ...
        ---
        耗时: ... 活跃: ...
        """
        if not self.tg_bin.exists() and not shutil.which("tg"):
            return False

        cmd = [str(self.tg_bin)] if self.tg_bin.exists() else ["tg"]
        
        # Prepare payload
        total_hours = metrics.total_duration_seconds / 3600.0
        active_hours = metrics.active_duration_seconds / 3600.0
        deep_hours = metrics.deep_work_seconds / 3600.0
        flow_str = f"{metrics.flow_streak_minutes:.0f}m"
        if metrics.longest_flow_session:
            flow_str += f" ({metrics.longest_flow_session.primary_app})"

        msg = (
            f"📅 【每日复盘速递 · {date_str}】\n\n"
            f"{brief_summary.strip()}\n"
            f"---\n"
            f"耗时: {total_hours:.1f}h | 活跃: {active_hours:.1f}h\n"
            f"精力利用效率: {metrics.energy_efficiency_pct}% | 产出/精力比: {metrics.output_energy_ratio}\n"
            f"有效专注时长: {deep_hours:.1f}h\n"
            f"最长连续心流区间: {flow_str}\n"
            f"打断碎裂指数: {metrics.fragmentation_count} 次"
        )

        try:
            proc = subprocess.run(
                [*cmd, msg],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15,
            )
            return proc.returncode == 0
        except Exception:
            return False
