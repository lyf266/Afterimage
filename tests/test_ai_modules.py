#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Afterimage AI & Output modules
"""

import sys
import unittest
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ai import PrivacySanitizer, PromptCatalog, AIClientFactory
from outputs import MarkdownReportGenerator, ObsidianVaultSync


class TestPrivacySanitizer(unittest.TestCase):
    def setUp(self):
        self.sanitizer = PrivacySanitizer(custom_words=["secret_project"])

    def test_redact_tokens(self):
        text = "Authorization: Bearer my_secret_token_1234567890"
        clean = self.sanitizer.sanitize(text)
        self.assertIn("[REDACTED]", clean)
        self.assertNotIn("my_secret_token_1234567890", clean)

    def test_redact_github_pat(self):
        text = "Token: ghp_123456789012345678901234567890"
        clean = self.sanitizer.sanitize(text)
        self.assertIn("[REDACTED]", clean)
        self.assertNotIn("ghp_123456789012345678901234567890", clean)

    def test_redact_custom_word(self):
        text = "Editing documentation for secret_project on desktop"
        clean = self.sanitizer.sanitize(text)
        self.assertIn("[REDACTED]", clean)
        self.assertNotIn("secret_project", clean)


class TestPromptCatalog(unittest.TestCase):
    def test_daily_prompt_format(self):
        prompt = PromptCatalog.DAILY_RETROSPECTIVE_USER.format(
            date="2026-10-31",
            total_duration="6h 30m",
            active_duration="5h 15m",
            switch_count=42,
            total_keystrokes=12500,
            avg_kpm="45.2",
            mouse_distance="350.5 m",
            category_breakdown="- **Dev**: 4h (61.5%)",
            top_applications="- Cursor: 3h (46.2%)",
            fragile_windows="- Hour 14:00: 12 switches",
        )
        self.assertIn("2026-10-31", prompt)
        self.assertIn("6h 30m", prompt)
        self.assertIn("Cursor", prompt)


class TestAIClientFactory(unittest.TestCase):
    def test_create_ollama_client(self):
        client = AIClientFactory.create("ollama", {"base_url": "http://localhost:11434", "model": "qwen2.5:7b"})
        self.assertEqual(client.model, "qwen2.5:7b")

    def test_invalid_provider(self):
        with self.assertRaises(ValueError):
            AIClientFactory.create("unsupported_provider")


if __name__ == "__main__":
    unittest.main()
