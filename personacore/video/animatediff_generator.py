"""
AnimateDiff video generator via Hugging Face diffusers.
Requires: torch, diffusers>=0.25, transformers, accelerate
"""

from __future__ import annotations

from pathlib import Path

from personacore.logging_module import get_logger
from .base_generator import BaseVideoGenerator, GenerationParams, GenerationResult
from .ffmpeg_pipeline import FFmpegPipeline

log = get_logger("video.animatediff")

MODEL_ID = "guoyww/animatediff-motion-adapter-v1-5-2"
BASE_MODEL = "SG161222/Realistic_Vision_V5.1_noVAE"


class AnimateDiffGenerator(BaseVideoGenerator):
    name = "AnimateDiff v1.5"
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
        from diffusers import AnimateDiffPipeline, MotionAdapter, EulerDiscreteScheduler
        from diffusers.utils import export_to_video
        from huggingface_hub import hf_hub_download
        from safetensors.torch import load_file

        log.info("Loading AnimateDiff pipeline")
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        adapter = MotionAdapter.from_pretrained(MODEL_ID, torch_dtype=dtype)
        self._pipe = AnimateDiffPipeline.from_pretrained(
            BASE_MODEL,
            motion_adapter=adapter,
            torch_dtype=dtype,
        )
        self._pipe.scheduler = EulerDiscreteScheduler.from_config(
            self._pipe.scheduler.config,
            timestep_spacing="linspace",
            beta_schedule="linear",
        )
        if torch.cuda.is_available():
            self._pipe = self._pipe.to("cuda")
            self._pipe.enable_vae_slicing()

        log.info("AnimateDiff pipeline ready")

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
        from diffusers.utils import export_to_video

        output_dir.mkdir(parents=True, exist_ok=True)

        if on_progress:
            on_progress(0.05, "Running AnimateDiff inference...")

        seed = params.seed if params.seed >= 0 else torch.randint(0, 2**32, (1,)).item()
        generator = torch.manual_seed(seed)

        num_frames = min(params.num_frames, 32)  # AnimateDiff limit

        def _step_cb(step, timestep, latents):
            if is_cancelled and is_cancelled():
                raise InterruptedError("Cancelled")
            if on_progress:
                frac = 0.05 + 0.8 * (step / params.num_inference_steps)
                on_progress(frac, f"Step {step}/{params.num_inference_steps}")

        try:
            output = self._pipe(
                prompt=params.prompt,
                negative_prompt=params.negative_prompt or "blurry, low quality, distorted",
                num_frames=num_frames,
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
            on_progress(0.88, "Exporting frames...")

        frames = output.frames[0]
        frames_dir = output_dir / "frames"
        frames_dir.mkdir(exist_ok=True)
        for i, frame in enumerate(frames):
            frame.save(frames_dir / f"frame_{i:05d}.png")

        if on_progress:
            on_progress(0.92, "Compositing video...")

        output_path = output_dir / "output.mp4"
        FFmpegPipeline().frames_to_video(frames_dir, output_path, fps=params.fps)

        if on_progress:
            on_progress(1.0, "Complete")

        return GenerationResult(
            success=output_path.exists(),
            output_path=output_path,
            frames_dir=frames_dir,
            duration_seconds=num_frames / params.fps,
            fps=params.fps,
            metadata={"model": "animatediff", "seed": seed},
        )

    def teardown(self) -> None:
        if self._pipe is not None:
            import torch
            del self._pipe
            self._pipe = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
