"""FFmpeg-based video compositing, transitions, and export pipeline."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from personacore.logging_module import get_logger

log = get_logger("video.ffmpeg")


class FFmpegPipeline:
    """Wrapper around FFmpeg for video operations."""

    def __init__(self) -> None:
        self._ffmpeg = shutil.which("ffmpeg")
        self._ffprobe = shutil.which("ffprobe")

    def is_available(self) -> bool:
        return self._ffmpeg is not None

    def frames_to_video(
        self,
        frames_dir: Path,
        output_path: Path,
        fps: int = 8,
        crf: int = 23,
        pattern: str = "frame_%05d.png",
    ) -> bool:
        if not self._ffmpeg:
            log.warning("FFmpeg not found")
            return False

        cmd = [
            self._ffmpeg, "-y",
            "-framerate", str(fps),
            "-i", str(frames_dir / pattern),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", str(crf),
            "-preset", "fast",
            "-movflags", "+faststart",
            str(output_path),
        ]
        return self._run(cmd)

    def add_audio(
        self,
        video_path: Path,
        audio_path: Path,
        output_path: Path,
    ) -> bool:
        if not self._ffmpeg:
            return False

        cmd = [
            self._ffmpeg, "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(output_path),
        ]
        return self._run(cmd)

    def concat_videos(
        self,
        video_paths: list[Path],
        output_path: Path,
        transition: str = "fade",
        transition_duration: float = 0.5,
    ) -> bool:
        if not self._ffmpeg or not video_paths:
            return False

        # Write concat list
        list_path = output_path.parent / "_concat_list.txt"
        with list_path.open("w") as f:
            for vp in video_paths:
                f.write(f"file '{vp.absolute()}'\n")

        cmd = [
            self._ffmpeg, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_path),
            "-c", "copy",
            str(output_path),
        ]
        ok = self._run(cmd)
        list_path.unlink(missing_ok=True)
        return ok

    def export_gif(
        self,
        video_path: Path,
        output_path: Path,
        fps: int = 10,
        width: int = 480,
    ) -> bool:
        if not self._ffmpeg:
            return False

        palette_path = output_path.parent / "_palette.png"
        # Generate palette
        cmd1 = [
            self._ffmpeg, "-y",
            "-i", str(video_path),
            "-vf", f"fps={fps},scale={width}:-1:flags=lanczos,palettegen",
            str(palette_path),
        ]
        if not self._run(cmd1):
            return False

        # Apply palette
        cmd2 = [
            self._ffmpeg, "-y",
            "-i", str(video_path),
            "-i", str(palette_path),
            "-filter_complex", f"fps={fps},scale={width}:-1:flags=lanczos[x];[x][1:v]paletteuse",
            str(output_path),
        ]
        ok = self._run(cmd2)
        palette_path.unlink(missing_ok=True)
        return ok

    def export_webm(
        self,
        video_path: Path,
        output_path: Path,
        crf: int = 33,
    ) -> bool:
        if not self._ffmpeg:
            return False

        cmd = [
            self._ffmpeg, "-y",
            "-i", str(video_path),
            "-c:v", "libvpx-vp9",
            "-crf", str(crf),
            "-b:v", "0",
            "-pix_fmt", "yuv420p",
            str(output_path),
        ]
        return self._run(cmd)

    def get_video_info(self, video_path: Path) -> dict:
        if not self._ffprobe:
            return {}
        import json
        cmd = [
            self._ffprobe, "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            str(video_path),
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            data = json.loads(result.stdout)
            streams = data.get("streams", [])
            video = next((s for s in streams if s.get("codec_type") == "video"), {})
            return {
                "width": video.get("width", 0),
                "height": video.get("height", 0),
                "fps": eval(video.get("r_frame_rate", "0/1")),  # e.g. "24/1"
                "duration": float(video.get("duration", 0)),
                "codec": video.get("codec_name", ""),
            }
        except Exception as e:
            log.warning("ffprobe failed: %s", e)
            return {}

    def _run(self, cmd: list[str]) -> bool:
        log.debug("FFmpeg: %s", " ".join(cmd[:6]) + "...")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            if result.returncode != 0:
                log.error("FFmpeg error: %s", result.stderr[-500:])
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            log.error("FFmpeg timed out")
            return False
        except Exception as e:
            log.error("FFmpeg exception: %s", e)
            return False
