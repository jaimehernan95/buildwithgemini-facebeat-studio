import subprocess
from pathlib import Path
import pytest
from app.config import settings
from app.services.video_renderer import VideoRenderer


def test_video_renderer_transcode(tmp_path):
    """Test generating a short test video and running vertical 9:16 rendering with FFmpeg."""
    raw_video = tmp_path / "test_raw.webm"
    output_clip = tmp_path / "test_vertical.mp4"

    # Generate a 1-second synthetic WebM video using FFmpeg (libvpx-vp9 matching browser MediaRecorder)
    gen_cmd = [
        "/usr/bin/ffmpeg",
        "-y",
        "-f", "lavfi",
        "-i", "testsrc=duration=1:size=640x360:rate=30",
        "-c:v", "libvpx-vp9",
        str(raw_video),
    ]
    subprocess.run(gen_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert raw_video.exists()

    result = VideoRenderer.render_vertical_clip(
        input_video_path=raw_video,
        output_clip_path=output_clip,
        score=12500,
        max_combo=45,
        track_title="Test Track",
        player_name="Test Champion",
    )

    assert result["success"] is True
    assert output_clip.exists()
    assert output_clip.stat().st_size > 1000
