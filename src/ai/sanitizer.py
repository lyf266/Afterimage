#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Privacy Sanitizer for Afterimage
Ensures window captions, paths, and sensitive user tokens are scrubbed
prior to sending prompt payloads to local or cloud LLM backends.
"""

import re
from typing import List, Optional


class PrivacySanitizer:
    DEFAULT_PATTERNS = [
        re.compile(r"(?i)bearer\s+[a-z0-9_\-\.]+", re.IGNORECASE),
        re.compile(r"ghp_[a-zA-Z0-9]{20,}", re.IGNORECASE),
        re.compile(r"sk-[a-zA-Z0-9]{20,}", re.IGNORECASE),
        re.compile(r"(?i)password[=:]\s*[\S]+", re.IGNORECASE),
        re.compile(r"/home/[a-zA-Z0-9_\-]+/", re.IGNORECASE),
        re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", re.IGNORECASE),
    ]

    def __init__(self, custom_patterns: Optional[List[str]] = None, custom_words: Optional[List[str]] = None):
        self.patterns = list(self.DEFAULT_PATTERNS)
        if custom_patterns:
            for p in custom_patterns:
                try:
                    self.patterns.append(re.compile(p))
                except re.error:
                    pass
        self.custom_words = custom_words or []

    def sanitize(self, text: str) -> str:
        if not text:
            return ""

        result = text
        for pat in self.patterns:
            result = pat.sub("[REDACTED]", result)

        for word in self.custom_words:
            if word and word in result:
                result = result.replace(word, "[REDACTED]")

        return result
