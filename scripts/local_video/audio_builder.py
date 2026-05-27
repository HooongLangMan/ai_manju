import json
from pathlib import Path
import subprocess

from scripts.local_video.project_paths import ProjectPaths
from scripts.local_video.shots import load_shots


VOICE_MAP = {
    "female_narrator": "Tingting",
    "system_voice": "Meijia",
    "male_regent": "Sinji",
}


def resolve_voice(voice_key: str) -> str:
    try:
        return VOICE_MAP[voice_key]
    except KeyError as exc:
        raise ValueError(f"Unknown voice key: {voice_key}") from exc


def build_say_command(voice_name: str, text: str, output_path: Path) -> list[str]:
    return ["say", "-v", voice_name, "-o", str(output_path), text]


def measure_audio_duration(audio_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return round(float(result.stdout.strip()), 3)


def build_project_audio(paths: ProjectPaths) -> dict[str, float]:
    paths.ensure_generated_dirs()
    shots = load_shots(paths.shots_file)
    durations: dict[str, float] = {}

    for shot in shots:
        output_path = paths.audio_dir / f"{shot.id}.aiff"
        subprocess.run(
            build_say_command(resolve_voice(shot.voice), shot.dialogue, output_path),
            check=True,
        )
        durations[shot.id] = measure_audio_duration(output_path)

    paths.durations_file.write_text(
        json.dumps(durations, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return durations
