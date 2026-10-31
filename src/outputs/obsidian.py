#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obsidian Vault Sync for Afterimage
Injects or appends daily retrospective sections into Obsidian Daily Notes.
"""

from pathlib import Path
from typing import Optional


class ObsidianVaultSync:
    def __init__(self, vault_path: Optional[str] = None):
        self.vault_path = Path(vault_path).expanduser() if vault_path else None

    def sync_daily_note(self, date_str: str, retrospective_content: str) -> Optional[Path]:
        if not self.vault_path or not self.vault_path.exists():
            return None

        # Standard daily note filename convention
        note_file = self.vault_path / f"{date_str}.md"
        block = (
            f"\n\n## 🧠 Afterimage Retrospective\n\n"
            f"{retrospective_content.strip()}\n"
        )

        if note_file.exists():
            original = note_file.read_text(encoding="utf-8")
            if "## 🧠 Afterimage Retrospective" in original:
                # Replace existing block if already present
                parts = original.split("## 🧠 Afterimage Retrospective")
                rest = parts[1].split("\n## ", 1)
                after = f"\n## {rest[1]}" if len(rest) > 1 else ""
                new_text = parts[0].rstrip() + block + after.lstrip()
                note_file.write_text(new_text, encoding="utf-8")
            else:
                note_file.write_text(original + block, encoding="utf-8")
        else:
            note_file.write_text(f"# Daily Note: {date_str}\n" + block, encoding="utf-8")

        return note_file
