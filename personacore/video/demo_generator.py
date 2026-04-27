"""
Demo generator — produces a test video using OpenCV and NumPy.
No external model required. Used when no diffusion backend is available.
"""

from __future__ import annotations

import math
import time
from pathlib import Path

import numpy as np

from personacore.logging_module import get_logger
from .base_generator import BaseVideoGenerator, GenerationParams, GenerationResult
from .ffmpeg_pipeline import FFmpegPipeline

log = get_logger("video.demo")


class DemoGenerator(BaseVideoGenerator):
    name = "Demo (No Model Required)"
    requires_gpu = False
    requires_diffusers = False

    def is_available(self) -> bool:
        try:
            import cv2
            import numpy
            return True
        except ImportError:
            return False

    def generate(
        self,
        params: GenerationParams,
        output_dir: Path,
        on_progress=None,
        is_cancelled=None,
    ) -> GenerationResult:
        import cv2

        output_dir.mkdir(parents=True, exist_ok=True)
        frames_dir = output_dir / "frames"
        frames_dir.mkdir(exist_ok=True)

        num_frames = params.num_frames
        w, h = params.width, params.height

        log.info("Demo generator: %d frames at %dx%d", num_frames, w, h)

        # Generate cinematic-looking frames using gradient animations
        palette = _get_palette(params.style_preset)

        for i in range(num_frames):
            if is_cancelled and is_cancelled():
                return GenerationResult(success=False, error="Cancelled")

            t = i / max(num_frames - 1, 1)
            frame = _render_frame(t, w, h, palette, params.prompt)

            frame_path = frames_dir / f"frame_{i:05d}.png"
            cv2.imwrite(str(frame_path), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))

            if on_progress:
                on_progress(0.1 + 0.7 * (i / num_frames), f"Rendering frame {i+1}/{num_frames}")

        if on_progress:
            on_progress(0.8, "Compositing video...")

        # Use FFmpeg to assemble frames
        pipeline = FFmpegPipeline()
        output_path = output_dir / "output.mp4"

        if pipeline.is_available():
            ok = pipeline.frames_to_video(
                frames_dir=frames_dir,
                output_path=output_path,
                fps=params.fps,
                crf=23,
            )
        else:
            # OpenCV fallback
            ok = _opencv_write_video(frames_dir, output_path, params.fps, w, h)

        if on_progress:
            on_progress(1.0, "Complete")

        if ok and output_path.exists():
            return GenerationResult(
                success=True,
                output_path=output_path,
                frames_dir=frames_dir,
                duration_seconds=params.duration_seconds,
                fps=params.fps,
            )
        return GenerationResult(success=False, error="Video assembly failed")


def _get_palette(style: str) -> list[tuple[int, int, int]]:
    palettes = {
        "cinematic": [(15, 10, 30), (80, 20, 120), (200, 100, 50)],
        "neon_noir": [(5, 0, 20), (0, 200, 255), (255, 0, 128)],
        "anime": [(255, 100, 150), (100, 150, 255), (255, 220, 100)],
        "abstract": [(20, 0, 60), (0, 255, 180), (255, 60, 0)],
        "documentary": [(40, 35, 30), (180, 160, 120), (220, 200, 160)],
    }
    return palettes.get(style, palettes["cinematic"])


def _render_frame(
    t: float,
    w: int,
    h: int,
    palette: list[tuple[int, int, int]],
    prompt: str,
) -> np.ndarray:
    frame = np.zeros((h, w, 3), dtype=np.float32)

    # Animated gradient background
    for y in range(h):
        for x in range(w):
            # Swirling gradient based on t
            cx, cy = w / 2, h / 2
            dx, dy = (x - cx) / w, (y - cy) / h
            angle = math.atan2(dy, dx) + t * math.pi * 2
            radius = math.sqrt(dx**2 + dy**2)

            wave = math.sin(angle * 3 + t * 6) * 0.5 + 0.5
            wave2 = math.sin(radius * 8 - t * 4) * 0.5 + 0.5
            blend = wave * 0.6 + wave2 * 0.4

            c1 = np.array(palette[0], dtype=np.float32)
            c2 = np.array(palette[1], dtype=np.float32)
            c3 = np.array(palette[2], dtype=np.float32)

            if blend < 0.5:
                color = c1 * (1 - blend * 2) + c2 * (blend * 2)
            else:
                color = c2 * (1 - (blend - 0.5) * 2) + c3 * ((blend - 0.5) * 2)

            # Vignette
            vignette = 1.0 - radius * 1.2
            vignette = max(0.0, vignette)
            frame[y, x] = color * vignette

    # Add scan line effect
    for y in range(0, h, 4):
        frame[y] *= 0.85

    return np.clip(frame, 0, 255).astype(np.uint8)


def _opencv_write_video(
    frames_dir: Path,
    output_path: Path,
    fps: int,
    w: int,
    h: int,
) -> bool:
    import cv2

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, (w, h))
    if not writer.isOpened():
        return False

    frame_paths = sorted(frames_dir.glob("frame_*.png"))
    for fp in frame_paths:
        img = cv2.imread(str(fp))
        if img is not None:
            writer.write(img)

    writer.release()
    return output_path.exists()
