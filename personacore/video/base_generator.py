"""Abstract base class for all video generators — the pluggable interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


@dataclass
class GenerationParams:
    prompt: str
    negative_prompt: str = ""
    resolution: tuple[int, int] = (512, 512)
    fps: int = 8
    duration_seconds: float = 3.0
    guidance_scale: float = 7.5
    num_inference_steps: int = 25
    seed: int = -1
    use_gpu: bool = True
    gpu_memory_budget_gb: float = 6.0
    style_preset: str = "cinematic"
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def num_frames(self) -> int:
        return max(1, int(self.duration_seconds * self.fps))

    @property
    def width(self) -> int:
        return self.resolution[0]

    @property
    def height(self) -> int:
        return self.resolution[1]


@dataclass
class GenerationResult:
    success: bool
    output_path: Path | None = None
    frames_dir: Path | None = None
    duration_seconds: float = 0.0
    fps: int = 8
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


ProgressCallback = Callable[[float, str], None]  # (0..1, message)
CancelledCheck = Callable[[], bool]


class BaseVideoGenerator(ABC):
    """
    Pluggable video generator interface.

    All generators must implement generate(). The UI never imports a concrete
    generator directly — only through the registry.
    """

    #: Human-readable name shown in the UI
    name: str = "Base Generator"

    #: Whether this generator requires GPU
    requires_gpu: bool = False

    #: Whether this generator requires diffusers/torch
    requires_diffusers: bool = False

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this generator can run in the current environment."""
        ...

    @abstractmethod
    def generate(
        self,
        params: GenerationParams,
        output_dir: Path,
        on_progress: ProgressCallback | None = None,
        is_cancelled: CancelledCheck | None = None,
    ) -> GenerationResult:
        """
        Generate a video from params. Write output to output_dir.
        Call on_progress(fraction, message) periodically.
        Check is_cancelled() and abort early if it returns True.
        """
        ...

    def setup(self) -> None:
        """Optional one-time setup (model loading, etc.)."""
        pass

    def teardown(self) -> None:
        """Optional cleanup."""
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"
