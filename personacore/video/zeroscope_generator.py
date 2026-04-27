"""
Zeroscope v2 XL video generator via Hugging Face diffusers.
Requires: torch, diffusers, transformers, accelerate
"""

from __future__ import annotations

from pathlib import Path

from personacore.logging_module import get_logger
from .base_generator import BaseVideoGenerator, GenerationParams, GenerationResult
from .ffmpeg_pipeline import FFmpegPipeline

log = get_logger("video.zeroscope")

MODEL_ID = "cerspense/zeroscope_v2_576w"


class ZeroscopeGenerator(BaseVideoGenerator):
    name = "Zeroscope v2 (Diffusers)"
    requires_gpu = True
    requires_diffusers = True

    def __init__(self) -> None:
        self._pipe = None

    def is_available(self) -> bool:
        try:
            import torch
            import diffusers
            return True
        except ImportError:
            return False

    def setup(self) -> None:
        if self._pipe is not None:
            return
        import torch
        from diffusers import DiffusionPipeline

        log.info("Loading Zeroscope pipeline: %s", MODEL_ID)
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        self._pipe = DiffusionPipeline.from_pretrained(
            MODEL_ID,
            torch_dtype=dtype,
        )
        if torch.cuda.is_available():
            self._pipe = self._pipe.to("cuda")
            self._pipe.enable_model_cpu_offload()
        log.info("Zeroscope pipeline loaded")

    def generate(
        self,
        params: GenerationParams,
        output_dir: Path,
        on_progress=None,
        is_cancelled=None,
    ) -> GenerationResult:
        if self._pipe is None:
            self.setup()

        import torch
        import numpy as np
        from PIL import Image

        output_dir.mkdir(parents=True, exist_ok=True)
        frames_dir = output_dir / "frames"
        frames_dir.mkdir(exist_ok=True)

        if on_progress:
            on_progress(0.05, "Running inference...")

        seed = params.seed if params.seed >= 0 else torch.randint(0, 2**32, (1,)).item()
        generator = torch.manual_seed(seed)

        def _step_cb(step, timestep, latents):
            if is_cancelled and is_cancelled():
                raise InterruptedError("Cancelled")
            if on_progress:
                frac = 0.05 + 0.75 * (step / params.num_inference_steps)
                on_progress(frac, f"Inference step {step}/{params.num_inference_steps}")

        try:
            output = self._pipe(
                prompt=params.prompt,
                negative_prompt=params.negative_prompt or "blurry, distorted, low quality",
                num_frames=params.num_frames,
                height=params.height,
                width=params.width,
                num_inference_steps=params.num_inference_steps,
                guidance_scale=params.guidance_scale,
                generator=generator,
                callback=_step_cb,
                callback_steps=1,
            )
        except InterruptedError:
            return GenerationResult(success=False, error="Cancelled")

        if on_progress:
            on_progress(0.82, "Saving frames...")

        frames = output.frames[0]
        for i, frame in enumerate(frames):
            if isinstance(frame, Image.Image):
                frame.save(frames_dir / f"frame_{i:05d}.png")
            else:
                img = Image.fromarray((np.array(frame) * 255).astype("uint8"))
                img.save(frames_dir / f"frame_{i:05d}.png")

        if on_progress:
            on_progress(0.88, "Compositing video...")

        pipeline = FFmpegPipeline()
        output_path = output_dir / "output.mp4"
        pipeline.frames_to_video(frames_dir, output_path, fps=params.fps)

        if on_progress:
            on_progress(1.0, "Complete")

        return GenerationResult(
            success=output_path.exists(),
            output_path=output_path,
            frames_dir=frames_dir,
            duration_seconds=params.duration_seconds,
            fps=params.fps,
            metadata={"model": MODEL_ID, "seed": seed},
        )

    def teardown(self) -> None:
        if self._pipe is not None:
            import torch
            del self._pipe
            self._pipe = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
