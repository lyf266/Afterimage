"""
Rich Terminal UI Dashboard for Afterimage.
Renders high-fidelity retrospective panels, metrics cards, session timelines, and Markdown.
"""

from typing import List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns

from .clustering import FlowMetrics, WorkSession


class TerminalDashboard:
    """
    Renders telemetry data, session clusters, and cognitive retrospectives to terminal using Rich.
    Supports English and Chinese localization.
    """

    I18N = {
        "en": {
            "header_title": "Afterimage · Cognitive Telemetry & Focus Audit",
            "header_sub": "Native KDE Wayland Cognitive Telemetry Engine",
            "card_time_title": "⏱️ Active / Total Time",
            "card_time_lock": "Locked: {m:.1f}m",
            "card_flow_title": "🌊 Longest Focus Streak",
            "card_flow_deep": "Focus Work: {h:.1f}h",
            "card_energy_title": "⚡ Energy Utilization",
            "card_energy_ratio": "Output/Energy: {ratio}",
            "card_frag_title": "🧩 Fragmentation Index",
            "card_frag_switches": "Context Switches: {switches}",
            "card_frag_unit": "times",
            "card_hardware_title": "⌨️ Hardware Dynamics",
            "card_hardware_keys": "keys",
            "card_hardware_mouse": "{meters:.1f}m mouse",
            "table_title": "🖥️ Work Sessions (Session Clusters)",
            "col_time": "Time Range",
            "col_app": "Application",
            "col_cat": "Category",
            "col_dur": "Duration",
            "col_kpm": "Keys / KPM",
            "col_title": "Window Caption / Task Summary",
            "panel_ai_title": "💡 AI Cognitive Retrospective Report",
        },
        "zh": {
            "header_title": "Afterimage (残影) · 认知复盘与效能审计",
            "header_sub": "Native KDE Wayland Cognitive Telemetry Engine",
            "card_time_title": "⏱️ 活跃/总时长",
            "card_time_lock": "锁屏: {m:.1f}m",
            "card_flow_title": "🌊 最长心流区间",
            "card_flow_deep": "有效专注: {h:.1f}h",
            "card_energy_title": "⚡ 精力利用效率",
            "card_energy_ratio": "产出/精力: {ratio}",
            "card_frag_title": "🧩 打断碎裂指数",
            "card_frag_switches": "上下文切换: {switches}",
            "card_frag_unit": "次",
            "card_hardware_title": "⌨️ 硬件交互强度",
            "card_hardware_keys": "键",
            "card_hardware_mouse": "{meters:.1f}m 鼠标",
            "table_title": "🖥️ 核心会话聚类 (Work Sessions)",
            "col_time": "时间段",
            "col_app": "应用",
            "col_cat": "分类",
            "col_dur": "时长",
            "col_kpm": "按键/KPM",
            "col_title": "主要内容 / 窗口标题",
            "panel_ai_title": "💡 AI 深度复盘与认知审计报告",
        },
    }

    def __init__(self, console: Optional[Console] = None, lang: str = "zh"):
        self.console = console or Console()
        self.lang = lang if lang in self.I18N else "zh"
        self.t = self.I18N[self.lang]

    def render_header(self, title: Optional[str] = None):
        disp_title = title or self.t["header_title"]
        p = Panel(
            Text(f"✨ {disp_title}", style="bold cyan", justify="center"),
            border_style="bright_blue",
            subtitle=f"[dim]{self.t['header_sub']}[/dim]",
        )
        self.console.print(p)

    def render_metrics_cards(self, metrics: FlowMetrics):
        total_hours = metrics.total_duration_seconds / 3600.0
        active_hours = metrics.active_duration_seconds / 3600.0
        locked_mins = metrics.locked_duration_seconds / 60.0

        card_time = Panel(
            f"[bold green]{active_hours:.1f}h[/bold green] / [dim]{total_hours:.1f}h[/dim]\n"
            f"[dim]{self.t['card_time_lock'].format(m=locked_mins)}[/dim]",
            title=self.t["card_time_title"],
            border_style="green",
        )

        longest_str = f"{metrics.flow_streak_minutes:.0f}m"
        if metrics.longest_flow_session:
            longest_str += f"\n[dim]({metrics.longest_flow_session.primary_app})[/dim]"
        card_flow = Panel(
            f"[bold magenta]{longest_str}[/bold magenta]\n"
            f"[dim]{self.t['card_flow_deep'].format(h=metrics.deep_work_seconds/3600.0)}[/dim]",
            title=self.t["card_flow_title"],
            border_style="magenta",
        )

        card_energy = Panel(
            f"[bold yellow]{metrics.energy_efficiency_pct}%[/bold yellow]\n"
            f"[dim]{self.t['card_energy_ratio'].format(ratio=metrics.output_energy_ratio)}[/dim]",
            title=self.t["card_energy_title"],
            border_style="yellow",
        )

        card_frag = Panel(
            f"[bold red]{metrics.fragmentation_count} {self.t['card_frag_unit']}[/bold red]\n"
            f"[dim]{self.t['card_frag_switches'].format(switches=metrics.cognitive_switches)}[/dim]",
            title=self.t["card_frag_title"],
            border_style="red" if metrics.fragmentation_count > 10 else "blue",
        )

        card_hardware = Panel(
            f"[bold cyan]{metrics.total_keys:,}[/bold cyan] {self.t['card_hardware_keys']}\n"
            f"[dim]{self.t['card_hardware_mouse'].format(meters=metrics.total_mouse_meters)}[/dim]",
            title=self.t["card_hardware_title"],
            border_style="cyan",
        )

        self.console.print(Columns([card_time, card_flow, card_energy, card_frag, card_hardware]))

    def render_sessions_table(self, sessions: List[WorkSession], limit: int = 10):
        table = Table(
            title=self.t["table_title"],
            border_style="bright_black",
            header_style="bold cyan",
            expand=True,
        )
        table.add_column(self.t["col_time"], style="dim", width=16)
        table.add_column(self.t["col_app"], style="bold yellow", width=14)
        table.add_column(self.t["col_cat"], style="magenta", width=12)
        table.add_column(self.t["col_dur"], justify="right", width=10)
        table.add_column(self.t["col_kpm"], justify="right", width=12)
        table.add_column(self.t["col_title"], style="white")

        display_sessions = sessions[:limit]
        for s in display_sessions:
            time_range = f"{s.start_time.strftime('%H:%M')} ~ {s.end_time.strftime('%H:%M')}"
            dur_str = f"{s.duration_minutes:.1f}m"
            kpm_str = f"{s.key_presses} ({s.kpm:.0f})"
            table.add_row(
                time_range,
                s.primary_app,
                s.category,
                dur_str,
                kpm_str,
                s.summary_title[:50],
            )

        self.console.print(table)

    def render_ai_retrospective(self, markdown_text: str):
        # Gracefully render Markdown using rich.markdown if pygments is available,
        # otherwise render formatted lines inside a stylish Panel
        renderable = None
        try:
            from rich.markdown import Markdown
            renderable = Markdown(markdown_text)
        except (ImportError, ModuleNotFoundError):
            renderable = Text(markdown_text, style="white")

        panel = Panel(
            renderable,
            title=self.t["panel_ai_title"],
            border_style="bright_cyan",
            padding=(1, 2),
        )
        self.console.print(panel)
