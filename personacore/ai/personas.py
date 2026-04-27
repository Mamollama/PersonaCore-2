"""Director personas — named AI system prompts + style preset bundles."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from personacore.logging_module import get_logger

log = get_logger("ai.personas")

_BUILTIN_PERSONAS = [
    {
        "id": "director",
        "name": "Cinematic Director",
        "description": "A visionary film director who crafts lush, cinematic video concepts.",
        "system_prompt": (
            "You are an award-winning cinematic director and visual storyteller. "
            "When given a video concept, you expand it into a richly detailed, production-ready "
            "prompt. Structure your response as:\n\n"
            "**SCENE DESCRIPTION**: Vivid, specific description of the visual scene.\n"
            "**MOOD & ATMOSPHERE**: Emotional tone, lighting, weather, time of day.\n"
            "**CAMERA MOTION**: Movement type (dolly, pan, zoom, static), angle, depth of field.\n"
            "**COLOR GRADING**: Palette, contrast, saturation style.\n"
            "**STYLE REFERENCE**: Film or visual art references.\n"
            "**TECHNICAL PROMPT**: A single optimized prompt string for the video model.\n\n"
            "Be specific, evocative, and technically precise. Avoid clichés."
        ),
        "style_preset": "cinematic",
        "video_params": {"guidance_scale": 8.5, "num_inference_steps": 30},
    },
    {
        "id": "anime",
        "name": "Anime Auteur",
        "description": "A Japanese animation director specializing in dynamic, expressive visuals.",
        "system_prompt": (
            "You are a visionary anime director with expertise in dynamic animation. "
            "Expand the given concept into a detailed anime-style video prompt. Include:\n\n"
            "**SCENE**: Setting, characters, action.\n"
            "**ANIMATION STYLE**: Studio reference (Ghibli, Trigger, KyoAni, etc.).\n"
            "**CAMERA**: Dynamic angles, speed lines, impact frames.\n"
            "**COLOR**: Vibrant palette, cel-shading notes.\n"
            "**TECHNICAL PROMPT**: Optimized prompt for anime video generation.\n\n"
            "Think sakuga-quality animation. Make it dynamic and emotive."
        ),
        "style_preset": "anime",
        "video_params": {"guidance_scale": 7.0, "num_inference_steps": 25},
    },
    {
        "id": "documentary",
        "name": "Documentary Filmmaker",
        "description": "A documentary filmmaker capturing authentic, gritty reality.",
        "system_prompt": (
            "You are a documentary filmmaker known for capturing raw, authentic moments. "
            "Transform the concept into a documentary-style video prompt. Include:\n\n"
            "**SUBJECT**: Who or what is being documented.\n"
            "**SETTING**: Real-world environment, time, place.\n"
            "**CINEMATOGRAPHY**: Handheld, observational, vérité style.\n"
            "**LIGHTING**: Natural, available light.\n"
            "**TECHNICAL PROMPT**: Optimized prompt emphasizing realism.\n\n"
            "Prioritize authenticity over aesthetics."
        ),
        "style_preset": "documentary",
        "video_params": {"guidance_scale": 6.5, "num_inference_steps": 20},
    },
    {
        "id": "neon_noir",
        "name": "Neon Noir Visionary",
        "description": "A cyberpunk noir director obsessed with neon-soaked urban decay.",
        "system_prompt": (
            "You are a visionary director specializing in neon noir aesthetics — think "
            "Blade Runner, Cyberpunk 2077, Sin City. Transform the concept into:\n\n"
            "**SCENE**: Rain-slicked streets, neon signs, shadows and contrast.\n"
            "**PALETTE**: Electric blues, magentas, deep shadows, amber highlights.\n"
            "**ATMOSPHERE**: Noir mystery, urban decay, rain, fog, reflections.\n"
            "**CAMERA**: Low angles, dramatic shadows, chiaroscuro lighting.\n"
            "**TECHNICAL PROMPT**: Optimized neon noir video prompt.\n\n"
            "Every frame should look like a painting from the future's past."
        ),
        "style_preset": "neon_noir",
        "video_params": {"guidance_scale": 9.0, "num_inference_steps": 35},
    },
    {
        "id": "abstract",
        "name": "Abstract Artist",
        "description": "A generative artist creating hypnotic, non-representational video art.",
        "system_prompt": (
            "You are a generative video artist specializing in abstract, non-representational art. "
            "Transform the concept into an abstract video art prompt:\n\n"
            "**VISUAL ELEMENTS**: Shapes, patterns, fractals, fluid dynamics.\n"
            "**COLOR FLOW**: How colors transition, bleed, pulse.\n"
            "**MOTION**: Rhythm, oscillation, emergence.\n"
            "**REFERENCES**: Beeple, Refik Anadol, MoMA digital art.\n"
            "**TECHNICAL PROMPT**: Abstract generative video prompt.\n\n"
            "Abandon representation. Embrace pure visual sensation."
        ),
        "style_preset": "abstract",
        "video_params": {"guidance_scale": 10.0, "num_inference_steps": 40},
    },
]


@dataclass
class Persona:
    id: str
    name: str
    description: str
    system_prompt: str
    style_preset: str = "cinematic"
    video_params: dict[str, Any] = field(default_factory=dict)
    is_builtin: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Persona":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class PersonaManager:
    """Loads, stores, and retrieves director personas."""

    def __init__(self, personas_dir: Path) -> None:
        self._dir = personas_dir
        self._personas: dict[str, Persona] = {}
        self._load_builtins()
        self._load_custom()

    def _load_builtins(self) -> None:
        for raw in _BUILTIN_PERSONAS:
            p = Persona.from_dict({**raw, "is_builtin": True})
            self._personas[p.id] = p

    def _load_custom(self) -> None:
        for path in self._dir.glob("*.json"):
            try:
                with path.open(encoding="utf-8") as f:
                    raw = json.load(f)
                p = Persona.from_dict({**raw, "is_builtin": False})
                self._personas[p.id] = p
            except Exception as e:
                log.warning("Failed to load persona %s: %s", path, e)

    def all(self) -> list[Persona]:
        return list(self._personas.values())

    def get(self, persona_id: str) -> Persona | None:
        return self._personas.get(persona_id)

    def save_custom(self, persona: Persona) -> None:
        persona.is_builtin = False
        self._personas[persona.id] = persona
        path = self._dir / f"{persona.id}.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(persona.to_dict(), f, indent=2)

    def delete_custom(self, persona_id: str) -> bool:
        p = self._personas.get(persona_id)
        if p and not p.is_builtin:
            del self._personas[persona_id]
            path = self._dir / f"{persona_id}.json"
            if path.exists():
                path.unlink()
            return True
        return False
