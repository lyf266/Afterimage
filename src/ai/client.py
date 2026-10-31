#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Client Factory and Backend Adapters for Afterimage
Supports local Ollama, Google Gemini API, and OpenAI-compatible endpoints (DeepSeek, etc.)
using pure Python standard library (urllib.request) to maintain zero mandatory external dependencies.
"""

import json
import os
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseAIClient(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Execute text completion / chat request."""
        pass


class OllamaClient(BaseAIClient):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:7b", temperature: float = 0.3):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": {
                "temperature": self.temperature,
            },
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("message", {}).get("content", "")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Ollama connection error at {url}: {e}")


class GeminiClient(BaseAIClient):
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash", temperature: float = 0.3):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model = model
        self.temperature = temperature
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not configured or provided.")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "system_instruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": self.temperature
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
                return ""
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            raise RuntimeError(f"Gemini API HTTP {e.code}: {err_body}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Gemini API connection error: {e}")


class OpenAICompatibleClient(BaseAIClient):
    def __init__(
        self,
        base_url: str = "https://api.deepseek.com/v1",
        api_key: Optional[str] = None,
        model: str = "deepseek-chat",
        temperature: float = 0.3,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        self.temperature = temperature
        if not self.api_key:
            raise ValueError("API Key not provided for OpenAI compatible endpoint.")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
                return ""
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            raise RuntimeError(f"API HTTP {e.code}: {err_body}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"API connection error: {e}")


class AIClientFactory:
    @staticmethod
    def create(provider: str = "ollama", config: Optional[Dict[str, Any]] = None) -> BaseAIClient:
        cfg = config or {}
        provider = provider.lower()

        if provider == "ollama":
            return OllamaClient(
                base_url=cfg.get("base_url", "http://localhost:11434"),
                model=cfg.get("model", "qwen2.5:7b"),
                temperature=cfg.get("temperature", 0.3),
            )
        elif provider == "gemini":
            return GeminiClient(
                api_key=cfg.get("api_key") or os.environ.get(cfg.get("api_key_env", "GEMINI_API_KEY")),
                model=cfg.get("model", "gemini-2.5-flash"),
                temperature=cfg.get("temperature", 0.3),
            )
        elif provider in ("deepseek", "openai"):
            return OpenAICompatibleClient(
                base_url=cfg.get("base_url", "https://api.deepseek.com/v1"),
                api_key=cfg.get("api_key") or os.environ.get(cfg.get("api_key_env", "DEEPSEEK_API_KEY")),
                model=cfg.get("model", "deepseek-chat"),
                temperature=cfg.get("temperature", 0.3),
            )
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")
