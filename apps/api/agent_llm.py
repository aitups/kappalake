"""OpenAI-compatible LLM provider for FastPath agents (backs Hayai)."""
import os

import openai
from fastpath.llm_provider import LLMProvider


class OpenAICompatibleProvider(LLMProvider):
    """LLMProvider that targets any OpenAI-compatible endpoint (Hayai llm service)."""

    def __init__(self, config=None):
        cfg = config or {}
        self.base_url = cfg.get("base_url", os.getenv("LLM_API_URL", "http://llm:8080/v1"))
        self.api_key = cfg.get("api_key", os.getenv("LLM_API_KEY", "sk-no-key-required"))
        self.model = cfg.get("model", os.getenv("LLM_MODEL", "SmolLM2-135M-Instruct-Q4_K_M"))
        self.client = openai.OpenAI(base_url=self.base_url, api_key=self.api_key)

    def generate(self, prompt: str, **kwargs) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=float(kwargs.get("temperature", 0.3)),
            max_tokens=int(kwargs.get("max_tokens", 512)),
        )
        return (response.choices[0].message.content or "").strip()
