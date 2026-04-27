"""Video export module — format conversion and resolution scaling."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from personacore.logging_module import get_logger
from personacore.video.ffmpeg_pipeline import FFmpegPipeline

log = get_logger("export")


class ExportFormat(str, Enum):
    MP4 = "mp4"
    GIF = "gif"
    WEBM = "webm"


@dataclass
class ExportOptions:
    format: ExportFormat = ExportFormat.MP4
    resolution: tuple[int, int] | None = None  # None = keep original
    fps: int | None = None
    crf: int = 23
    gif_width: int = 480


class Exporter:
    def __init__(self) -> None:
        self._pipeline = FFmpegPipeline()

    def export(
        self,
        source_path: Path,
        dest_path: Path,
        options: ExportOptions,
    ) -> bool:
        if not source_path.exists():
            log.error("Source not found: %s", source_path)
            return False

        log.info("Exporting %s -> %s (%s)", source_path.name, dest_path.name, options.format)

        if options.format == ExportFormat.MP4:
            return self._export_mp4(source_path, dest_path, options)
        elif options.format == ExportFormat.GIF:
            return self._pipeline.export_gif(
                source_path, dest_path,
                fps=options.fps or 10,
                width=options.gif_width,
            )
        elif options.format == ExportFormat.WEBM:
            return self._pipeline.export_webm(source_path, dest_path, crf=options.crf)

        return False

    def _export_mp4(self, source: Path, dest: Path, options: ExportOptions) -> bool:
        import shutil
        import subprocess

        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            shutil.copy2(source, dest)
            return True

        vf_parts = []
        if options.resolution:
            w, h = options.resolution
            vf_parts.append(f"scale={w}:{h}")
        if options.fps:
            vf_parts.append(f"fps={options.fps}")

        cmd = [ffmpeg, "-y", "-i", str(source)]
        if vf_parts:
            cmd += ["-vf", ",".join(vf_parts)]
        cmd += [
            "-c:v", "libx264",
            "-crf", str(options.crf),
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            "-movflags", "+faststart",
            str(dest),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, timeout=120)
            return result.returncode == 0
        except Exception as e:
            log.error("Export MP4 failed: %s", e)
            return False
