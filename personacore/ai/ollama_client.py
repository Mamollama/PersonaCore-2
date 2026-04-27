"""Low-level Ollama REST client with streaming support."""

from __future__ import annotations

import json
from collections.abc import Generator
from typing import Any

import httpx

from personacore.logging_module import get_logger

log = get_logger("ai.ollama")


class OllamaError(Exception):
    pass


class OllamaClient:
    """Thin wrapper around Ollama's REST API."""

    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    # ------------------------------------------------------------------ health
    def is_alive(self) -> bool:
        try:
            r = self._client.get("/", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    # ----------------------------------------------------------------- models
    def list_models(self) -> list[dict[str, Any]]:
        try:
            r = self._client.get("/api/tags")
            r.raise_for_status()
            return r.json().get("models", [])
        except httpx.HTTPError as e:
            raise OllamaError(f"Failed to list models: {e}") from e

    def pull_model(self, name: str) -> Generator[dict[str, Any], None, None]:
        with self._client.stream("POST", "/api/pull", json={"name": name}) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line:
                    yield json.loads(line)

    # ----------------------------------------------------------------- generate
    def generate_stream(
        self,
        model: str,
        prompt: str,
        system: str = "",
        options: dict[str, Any] | None = None,
    ) -> Generator[str, None, None]:
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": True,
        }
        if system:
            payload["system"] = system
        if options:
            payload["options"] = options

        log.debug("Streaming generate: model=%s prompt_len=%d", model, len(prompt))
        try:
            with self._client.stream("POST", "/api/generate", json=payload) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if line:
                        data = json.loads(line)
                        chunk = data.get("response", "")
                        if chunk:
                            yield chunk
                        if data.get("done"):
                            break
        except httpx.HTTPError as e:
            raise OllamaError(f"Generate request failed: {e}") from e

    def generate(
        self,
        model: str,
        prompt: str,
        system: str = "",
        options: dict[str, Any] | None = None,
    ) -> str:
        return "".join(self.generate_stream(model, prompt, system, options))

    # ------------------------------------------------------------------- chat
    def chat_stream(
        self,
        model: str,
        messages: list[dict[str, str]],
        options: dict[str, Any] | None = None,
    ) -> Generator[str, None, None]:
        payload: dict[str, Any] = {"model": model, "messages": messages, "stream": True}
        if options:
            payload["options"] = options

        try:
            with self._client.stream("POST", "/api/chat", json=payload) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if line:
                        data = json.loads(line)
                        chunk = data.get("message", {}).get("content", "")
                        if chunk:
                            yield chunk
                        if data.get("done"):
                            break
        except httpx.HTTPError as e:
            raise OllamaError(f"Chat request failed: {e}") from e

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "OllamaClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
