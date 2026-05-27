from scripts.local_video.rendering import (
    build_motion_filter,
    build_subtitles,
    compute_final_duration,
)
from scripts.local_video.shots import Shot


def test_compute_final_duration_respects_audio_tail_buffer() -> None:
    assert compute_final_duration(5.0, 3.0) == 5.0
    assert compute_final_duration(5.0, 5.2) == 5.8


def test_build_subtitles_uses_cumulative_shot_timing() -> None:
    shots = [
        Shot(
            id="shot-001",
            image="stills/shot-001.png",
            duration_sec=6.0,
            camera_motion="static",
            voice="female_narrator",
            dialogue="a",
            subtitle="第一句",
        ),
        Shot(
            id="shot-002",
            image="stills/shot-002.png",
            duration_sec=5.0,
            camera_motion="static",
            voice="system_voice",
            dialogue="b",
            subtitle="第二句",
        ),
    ]
    final_durations = {"shot-001": 6.0, "shot-002": 5.8}

    subtitles = build_subtitles(shots, final_durations)

    assert "00:00:00,000 --> 00:00:06,000" in subtitles
    assert "00:00:06,000 --> 00:00:11,800" in subtitles
    assert "第一句" in subtitles
    assert "第二句" in subtitles


def test_build_motion_filter_rejects_unknown_motion() -> None:
    try:
        build_motion_filter("orbit", 5.0)
    except ValueError as exc:
        assert "Unknown camera motion" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
