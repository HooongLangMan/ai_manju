from pathlib import Path

from scripts.local_video.shots import Shot


FPS = 24
AUDIO_TAIL_BUFFER = 0.6


def compute_final_duration(min_duration: float, audio_duration: float) -> float:
    return round(max(min_duration, audio_duration + AUDIO_TAIL_BUFFER), 3)


def format_srt_timestamp(seconds: float) -> str:
    total_ms = int(round(seconds * 1000))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def build_subtitles(shots: list[Shot], final_durations: dict[str, float]) -> str:
    cursor = 0.0
    blocks: list[str] = []
    for index, shot in enumerate(shots, start=1):
        start = cursor
        end = cursor + final_durations[shot.id]
        blocks.append(
            "\n".join(
                [
                    str(index),
                    f"{format_srt_timestamp(start)} --> {format_srt_timestamp(end)}",
                    shot.subtitle,
                ]
            )
        )
        cursor = end
    return "\n\n".join(blocks) + "\n"


def build_motion_filter(camera_motion: str, duration_sec: float) -> str:
    if camera_motion == "static":
        return (
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,fps=24,format=yuv420p"
        )
    if camera_motion == "slow_push_in":
        frames = max(int(duration_sec * FPS), 1)
        return (
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            f"zoompan=z='min(zoom+0.0007,1.08)':d={frames}:s=1080x1920:fps=24,"
            "format=yuv420p"
        )
    if camera_motion == "slow_pan_left":
        return (
            "scale=1188:2112,"
            f"crop=1080:1920:x='(in_w-out_w)*(1-min(t/{duration_sec},1))':"
            "y='(in_h-out_h)/2',fps=24,format=yuv420p"
        )
    if camera_motion == "slow_pan_right":
        return (
            "scale=1188:2112,"
            f"crop=1080:1920:x='(in_w-out_w)*min(t/{duration_sec},1)':"
            "y='(in_h-out_h)/2',fps=24,format=yuv420p"
        )
    raise ValueError(f"Unknown camera motion: {camera_motion}")


def build_clip_command(
    image_path: Path,
    audio_path: Path,
    output_path: Path,
    camera_motion: str,
    duration_sec: float,
) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        str(image_path),
        "-i",
        str(audio_path),
        "-vf",
        build_motion_filter(camera_motion, duration_sec),
        "-t",
        str(duration_sec),
        "-r",
        str(FPS),
        "-pix_fmt",
        "yuv420p",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        str(output_path),
    ]


def build_concat_manifest(clip_paths: list[Path]) -> str:
    return "\n".join(f"file '{path}'" for path in clip_paths) + "\n"
