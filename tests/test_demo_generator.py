from __future__ import annotations

import cv2

from personacore.video.base_generator import GenerationParams
from personacore.video.demo_generator import DemoGenerator
from personacore.video.ffmpeg_pipeline import FFmpegPipeline
from personacore.video.registry import get_registry


def test_demo_backend_generates_readable_video(tmp_path) -> None:
    progress: list[tuple[float, str]] = []
    params = GenerationParams(
        prompt="A tiny backend smoke test",
        resolution=(64, 64),
        fps=4,
        duration_seconds=1,
        style_preset="cinematic",
    )

    result = DemoGenerator().generate(
        params,
        tmp_path,
        on_progress=lambda fraction, message: progress.append((fraction, message)),
    )

    assert result.success, result.error
    assert result.output_path is not None
    assert result.output_path.exists()
    assert result.output_path.stat().st_size > 0
    assert progress[-1] == (1.0, "Complete")

    cap = cv2.VideoCapture(str(result.output_path))
    assert cap.isOpened()
    assert int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) == 64
    assert int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) == 64
    assert cap.get(cv2.CAP_PROP_FRAME_COUNT) >= 1
    cap.release()

    info = FFmpegPipeline().get_video_info(result.output_path)
    assert info["width"] == 64
    assert info["height"] == 64
    assert info["duration"] > 0


def test_registry_can_create_demo_backend() -> None:
    generator = get_registry().create("demo")

    assert isinstance(generator, DemoGenerator)
    assert generator.is_available()
