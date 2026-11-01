"""
Outputs Package for Afterimage
Handles export to Markdown reports, Obsidian vaults, and structured sinks.
"""

from .markdown import MarkdownReportGenerator
from .obsidian import ObsidianVaultSync
from .exporter import MultiChannelExporter

__all__ = ["MarkdownReportGenerator", "ObsidianVaultSync", "MultiChannelExporter"]
