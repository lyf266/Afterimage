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
            period_str="2026-10-31",
            total_duration_hours=6.5,
            total_duration_mins=390.0,
            active_hours=5.25,
            active_mins=315.0,
            active_ratio=80.7,
            locked_mins=15.0,
            total_keys=12500,
            total_clicks=1500,
            total_meters=350.5,
            longest_flow_str="72 分钟",
            deep_work_str="5.2 小时",
            fragmentation_str="极低",
            frag_count=2,
            energy_eff_pct=85,
            output_energy_ratio=0.8,
            session_summary="1. [Orca] 10:00~11:12",
            deep_work_hours=5.2,
        )
        self.assertIn("2026-10-31", prompt)
        self.assertIn("12,500", prompt)
        self.assertIn("Orca", prompt)

    def test_daily_prompt_en_format(self):
        prompt = PromptCatalog.DAILY_RETROSPECTIVE_USER_EN.format(
            period_str="2026-10-31",
            total_duration_hours=6.5,
            total_duration_mins=390.0,
            active_hours=5.25,
            active_mins=315.0,
            active_ratio=80.7,
            locked_mins=15.0,
            total_keys=12500,
            total_clicks=1500,
            total_meters=350.5,
            longest_flow_str="72 mins",
            deep_work_str="5.2 hours",
            fragmentation_str="Very Low",
            frag_count=2,
            energy_eff_pct=85,
            output_energy_ratio=0.8,
            session_summary="1. [Orca] 10:00~11:12",
            deep_work_hours=5.2,
        )
        self.assertIn("2026-10-31", prompt)
        self.assertIn("Total Online Duration", prompt)
        self.assertIn("12,500 keystrokes", prompt)
        self.assertIn("Core Outputs & Key Milestones", prompt)


class TestAIClientFactory(unittest.TestCase):
    def test_create_ollama_client(self):
        client = AIClientFactory.create("ollama", {"base_url": "http://localhost:11434", "model": "qwen2.5:7b"})
        self.assertEqual(client.model, "qwen2.5:7b")

    def test_create_openrouter_client(self):
        client = AIClientFactory.create(
            "openrouter",
            {"api_key": "test_key", "model": "nvidia/nemotron-3.5-lightning:free"}
        )
        self.assertEqual(client.model, "nvidia/nemotron-3.5-lightning:free")
        self.assertEqual(client.api_key, "test_key")

    def test_invalid_provider(self):
        with self.assertRaises(ValueError):
            AIClientFactory.create("unsupported_provider")


if __name__ == "__main__":
    unittest.main()
