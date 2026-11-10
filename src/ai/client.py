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


def _get_urllib_opener():
    """
    Builds a urllib opener respecting system proxy environment variables or
    local proxy ports (such as v2rayA / clash on 127.0.0.1:20171).
    """
    http_proxy = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY") or os.environ.get("http_proxy") or os.environ.get("HTTP_PROXY")
    if not http_proxy:
        # Check standard local proxy port
        candidates = ["http://127.0.0.1:20171", "http://127.0.0.1:7890", "http://127.0.0.1:10808"]
        for p in candidates:
            try:
                import socket
                host, port = p.replace("http://", "").split(":")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.1)
                res = sock.connect_ex((host, int(port)))
                sock.close()
                if res == 0:
                    http_proxy = p
                    break
            except Exception:
                pass

    if http_proxy:
        proxy_handler = urllib.request.ProxyHandler({"http": http_proxy, "https": http_proxy})
        return urllib.request.build_opener(proxy_handler)
    return urllib.request.build_opener()


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
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("message", {}).get("content", "")
        except urllib.error.URLError as e:
            raise RuntimeError(
                f"❌ 本地 Ollama 服务未运行或无法连接 ({url}): {e}\n"
                f"提示: 请先运行 `ollama serve` 启动本地推理引擎，或使用 `--provider gemini` 切换为云端模型。"
            )
        except TimeoutError:
            raise RuntimeError(
                f"❌ 本地 Ollama 请求超时 (超过 30 秒)。请检查模型 {self.model} 是否加载过慢或显存不足。"
            )


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
            opener = _get_urllib_opener()
            with opener.open(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
                return ""
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            raise RuntimeError(f"❌ Gemini API HTTP {e.code}: {err_body}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"❌ Gemini 网络连接超时或失败: {e}\n提示: 请检查本地网络或代理设置 (127.0.0.1:20171)。")
        except TimeoutError:
            raise RuntimeError("❌ Gemini API 请求超时 (超过 45 秒)。未收到响应，已主动中断避免终端卡死。")


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
            opener = _get_urllib_opener()
            with opener.open(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
                return ""
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            raise RuntimeError(f"❌ OpenAI/DeepSeek API HTTP {e.code}: {err_body}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"❌ API 连接超时或失败: {e}\n提示: 请检查 API 密钥及代理连通性。")
        except TimeoutError:
            raise RuntimeError("❌ API 请求超时 (超过 45 秒)。未收到响应，已主动中断避免终端卡死。")


class OpenRouterClient(BaseAIClient):
    """
    OpenRouter client supporting OpenAI-compatible chat completions with
    automatic failover across OpenRouter :free models in case of rate limits (429/503).
    """
    DEFAULT_FREE_MODELS = [
        "nvidia/nemotron-3.5-lightning:free",
        "google/gemma-4-31b-it:free",
        "google/gemma-4-26b-a4b-it:free",
        "thinkingmachines/inkling-2-small:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "deepseek/deepseek-r1:free",
    ]

    def __init__(
        self,
        base_url: str = "https://openrouter.ai/api/v1",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.3,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.model = model or self.DEFAULT_FREE_MODELS[0]
        self.temperature = temperature
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not configured or provided.\n"
                "提示: 请配置环境变量 OPENROUTER_API_KEY 或在 ~/.config/afterimage/config.json 中指定。"
            )

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        models_to_try = [self.model]
        for fm in self.DEFAULT_FREE_MODELS:
            if fm not in models_to_try:
                models_to_try.append(fm)

        url = f"{self.base_url}/chat/completions"
        last_error = None

        for candidate_model in models_to_try:
            payload = {
                "model": candidate_model,
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
                    "HTTP-Referer": "https://github.com/lyf266/Afterimage",
                    "X-Title": "Afterimage Desktop",
                },
                method="POST",
            )

            try:
                opener = _get_urllib_opener()
                with opener.open(req, timeout=45) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    choices = data.get("choices", [])
                    if choices:
                        return choices[0].get("message", {}).get("content", "")
                    return ""
            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8")
                if e.code in (429, 503) and len(models_to_try) > 1:
                    last_error = f"Model {candidate_model} returned HTTP {e.code}: {err_body}"
                    continue
                raise RuntimeError(f"❌ OpenRouter API HTTP {e.code}: {err_body}")
            except urllib.error.URLError as e:
                raise RuntimeError(f"❌ OpenRouter API 连接失败: {e}\n提示: 请检查本地网络或代理设置 (127.0.0.1:20171)。")
            except TimeoutError:
                if len(models_to_try) > 1:
                    continue
                raise RuntimeError("❌ OpenRouter API 请求超时 (超过 45 秒)。未收到响应，已主动中断避免终端卡死。")

        if last_error:
            raise RuntimeError(f"❌ OpenRouter 免费模型调用失败: 所有候选模型均超出频率或繁忙 ({last_error})")
        return ""


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
        elif provider == "openrouter":
            return OpenRouterClient(
                base_url=cfg.get("base_url", "https://openrouter.ai/api/v1"),
                api_key=cfg.get("api_key") or os.environ.get(cfg.get("api_key_env", "OPENROUTER_API_KEY")),
                model=cfg.get("model", "nvidia/nemotron-3.5-lightning:free"),
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
