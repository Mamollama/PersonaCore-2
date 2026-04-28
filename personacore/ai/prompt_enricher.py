"""Prompt enrichment — sends raw user concept to Ollama, streams back enriched prompt."""

from __future__ import annotations

from collections.abc import Generator

from personacore.logging_module import get_logger

from .ollama_client import OllamaClient, OllamaError
from .personas import Persona

log = get_logger("ai.enricher")

_STYLE_MODIFIERS: dict[str, str] = {
    "cinematic": "cinematic, photorealistic, film grain, anamorphic lens, 4K",
    "anime": "anime style, vibrant colors, dynamic composition, sakuga quality",
    "documentary": "documentary, handheld camera, natural lighting, vérité, authentic",
    "neon_noir": "neon noir, cyberpunk, rain reflection, neon lights, dark atmosphere",
    "abstract": "abstract art, generative, fluid dynamics, hypnotic motion",
    "nature": "nature documentary, macro lens, golden hour, BBC Earth quality",
}


class PromptEnricher:
    """Handles the prompt enrichment pipeline through Ollama."""

    def __init__(self, client: OllamaClient) -> None:
        self._client = client

    def enrich_stream(
        self,
        raw_prompt: str,
        model: str,
        persona: Persona,
        cancelled: list[bool] | None = None,
    ) -> Generator[str, None, None]:
        """Stream enriched prompt chunks. Yields text chunks as they arrive."""

        user_message = (
            f"Create a detailed video generation prompt for this concept:\n\n{raw_prompt}\n\n"
            f"Style modifier: {_STYLE_MODIFIERS.get(persona.style_preset, '')}"
        )

        log.info("Enriching prompt with model=%s persona=%s", model, persona.id)
        try:
            for chunk in self._client.generate_stream(
                model=model,
                prompt=user_message,
                system=persona.system_prompt,
            ):
                if cancelled and cancelled[0]:
                    log.info("Enrichment cancelled by user")
                    return
                yield chunk
        except OllamaError as e:
            log.error("Enrichment failed: %s", e)
            raise

    def enrich(
        self,
        raw_prompt: str,
        model: str,
        persona: Persona,
    ) -> str:
        return "".join(self.enrich_stream(raw_prompt, model, persona))

    def extract_technical_prompt(self, enriched: str) -> str:
        """Extract the TECHNICAL PROMPT section from enriched output."""
        idx = enriched.upper().find("TECHNICAL PROMPT")
        if idx == -1:
            # Return last paragraph as fallback
            paragraphs = [p.strip() for p in enriched.split("\n\n") if p.strip()]
            return paragraphs[-1] if paragraphs else enriched.strip()

        after = enriched[idx:]
        # Skip the header line
        lines = after.split("\n")
        content_lines = []
        for line in lines[1:]:
            stripped = line.strip().lstrip(":-* ").strip()
            if stripped and not stripped.startswith("**"):
                content_lines.append(stripped)
            elif content_lines:
                break
        return " ".join(content_lines) or enriched.strip()
