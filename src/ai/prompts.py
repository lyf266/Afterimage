#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prompt Catalog for Afterimage AI Analysis.
Aligns with user retrospective requirements, flow metrics, and cognitive audit format.
"""


class PromptCatalog:
    SYSTEM_COGNITIVE_ANALYST = (
        "You are Afterimage (残影), an expert cognitive workflow analyst and desktop retrospective synthesis engine. "
        "Your task is to analyze local desktop activity telemetry (active windows, duration, "
        "keystroke cadences, mouse distances, context switches, and session clusters) and produce objective, "
        "high-signal, actionable retrospectives without sycophancy, buzzwords, or generic platitudes. "
        "All times should be presented in Beijing Time (UTC+8) when absolute times are referenced. "
        "Adhere strictly to factual evidence from the provided activity logs."
    )

    DAILY_RETROSPECTIVE_USER = """
请基于以下桌面活动遥测数据与心流聚类指标，生成今日的认知复盘与效能审计报告。

## 📊 统计周期与基础指标
- 统计周期: {period_str}
- 累计在线: {total_duration_hours:.2f}h ({total_duration_mins:.1f}m)
- 专注活跃时长: {active_hours:.2f}h ({active_mins:.1f}m, {active_ratio:.1f}%)
- 锁屏/挂起时长: {locked_mins:.1f}m
- 键盘敲击: {total_keys:,} 次，鼠标点击: {total_clicks:,} 次，鼠标位移: {total_meters:.1f} m
- 最长连续心流区间: {longest_flow_str}
- 有效专注时长: {deep_work_str}
- 打断碎裂指数: {fragmentation_str} (碎裂切换次数: {frag_count})
- 精力利用效率: {energy_eff_pct}%
- 产出/精力比: {output_energy_ratio}

## 🖥️ 核心活动会话聚类 (Work Sessions)
{session_summary}

---

请严格按照以下结构排版输出（采用中文，语言精炼收敛，先陈述事实后给出简要发散）：

## 📅 核心产出与重点事项
（结合上述活动会话聚类，归纳 3~5 项今天真正完成的核心产出与工程推进，注明对应的时间段区间与主要软件）

## 📊 效能与精力审计
- **耗时**: 累计在线 {total_duration_hours:.2f}h，活跃专注 {active_hours:.2f}h，按键 {total_keys:,} 次，鼠标位移 {total_meters:.1f} m
- **效率**: （客观评价今日核心工程与事务推进成果）
- **精力利用效率**: {energy_eff_pct}%    **产出/精力比**: {output_energy_ratio}
- **有效专注时长（真正高质量、抗打断的核心产出时间）**: 约 {deep_work_hours:.1f} 小时
- **最长连续心流区间**: {longest_flow_str}
- **打断碎裂指数**: （分析碎裂情况与注意力连续度）
- **浅层沟通/维护时长**: （评估非核心消耗）
- **与个人目标的契合度**: （评估产出与核心发展目标的契合度）

## 💡 总结和建议
- **总结**: （客观复盘今日得失）
- **建议**: （列出 2-3 条高杠杆的明日改进建议）
"""

    TELEGRAM_BRIEF_TEMPLATE = """📅
{key_events}
---
耗时: {total_hours:.1f}h  活跃: {active_hours:.1f}h
精力利用效率: {energy_eff_pct}%  产出/精力比: {output_energy_ratio}
有效专注时长: {deep_work_hours:.1f}h
最长连续心流: {longest_flow_str}
打断碎裂指数: {fragmentation_summary}
💡 建议: {top_advice}
"""

    NATURAL_LANGUAGE_QUERY = """
You have access to the user's desktop activity telemetry database for the specified timeframe.

## Telemetry Context
{context_data}

## User Question
{user_query}

Provide a direct, factual, and concise answer based strictly on the telemetry evidence above.
"""
