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
    """

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()

    def render_header(self, title: str = "Afterimage (残影) · 认知复盘与效能审计"):
        p = Panel(
            Text(f"✨ {title}", style="bold cyan", justify="center"),
            border_style="bright_blue",
            subtitle="[dim]Native KDE Wayland Cognitive Telemetry Engine[/dim]",
        )
        self.console.print(p)

    def render_metrics_cards(self, metrics: FlowMetrics):
        total_hours = metrics.total_duration_seconds / 3600.0
        active_hours = metrics.active_duration_seconds / 3600.0
        locked_mins = metrics.locked_duration_seconds / 60.0

        card_time = Panel(
            f"[bold green]{active_hours:.1f}h[/bold green] / [dim]{total_hours:.1f}h[/dim]\n"
            f"[dim]锁屏: {locked_mins:.1f}m[/dim]",
            title="⏱️ 活跃/总时长",
            border_style="green",
        )

        longest_str = f"{metrics.flow_streak_minutes:.0f}m"
        if metrics.longest_flow_session:
            longest_str += f"\n[dim]({metrics.longest_flow_session.primary_app})[/dim]"
        card_flow = Panel(
            f"[bold magenta]{longest_str}[/bold magenta]\n"
            f"[dim]有效专注: {metrics.deep_work_seconds/3600.0:.1f}h[/dim]",
            title="🌊 最长心流区间",
            border_style="magenta",
        )

        card_energy = Panel(
            f"[bold yellow]{metrics.energy_efficiency_pct}%[/bold yellow]\n"
            f"[dim]产出/精力: {metrics.output_energy_ratio}[/dim]",
            title="⚡ 精力利用效率",
            border_style="yellow",
        )

        card_frag = Panel(
            f"[bold red]{metrics.fragmentation_count} 次[/bold red]\n"
            f"[dim]上下文切换: {metrics.cognitive_switches}[/dim]",
            title="🧩 打断碎裂指数",
            border_style="red" if metrics.fragmentation_count > 10 else "blue",
        )

        card_hardware = Panel(
            f"[bold cyan]{metrics.total_keys:,}[/bold cyan] 键\n"
            f"[dim]{metrics.total_mouse_meters:.1f}m 鼠标[/dim]",
            title="⌨️ 硬件交互强度",
            border_style="cyan",
        )

        self.console.print(Columns([card_time, card_flow, card_energy, card_frag, card_hardware]))

    def render_sessions_table(self, sessions: List[WorkSession], limit: int = 10):
        table = Table(
            title="🖥️ 核心会话聚类 (Work Sessions)",
            border_style="bright_black",
            header_style="bold cyan",
            expand=True,
        )
        table.add_column("时间段", style="dim", width=16)
        table.add_column("应用", style="bold yellow", width=14)
        table.add_column("分类", style="magenta", width=12)
        table.add_column("时长", justify="right", width=10)
        table.add_column("按键/KPM", justify="right", width=12)
        table.add_column("主要内容 / 窗口标题", style="white")

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
            title="💡 AI 深度复盘与认知审计报告",
            border_style="bright_cyan",
            padding=(1, 2),
        )
        self.console.print(panel)
