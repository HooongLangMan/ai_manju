#!/usr/bin/env python3
from argparse import ArgumentParser
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.local_video.project_paths import ProjectPaths
from scripts.local_video.rendering import (
    build_clip_command,
    build_concat_manifest,
    build_subtitles,
    compute_final_duration,
)
from scripts.local_video.shots import load_shots


def load_durations(path: Path) -> dict[str, float]:
    if not path.exists():
        raise FileNotFoundError(f"Missing durations.json: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {shot_id: float(duration) for shot_id, duration in payload.items()}


def render_project_video(paths: ProjectPaths) -> Path:
    paths.ensure_generated_dirs()
    shots = load_shots(paths.shots_file)
    durations = load_durations(paths.durations_file)

    final_durations: dict[str, float] = {}
    clip_paths: list[Path] = []
    for shot in shots:
        audio_path = paths.audio_dir / f"{shot.id}.aiff"
        if not audio_path.exists():
            raise FileNotFoundError(f"Missing audio file: {audio_path}")

        final_duration = compute_final_duration(shot.duration_sec, durations[shot.id])
        final_durations[shot.id] = final_duration

        clip_path = paths.build_dir / f"{shot.id}.mp4"
        subprocess.run(
            build_clip_command(
                image_path=paths.project_dir / shot.image,
                audio_path=audio_path,
                output_path=clip_path,
                camera_motion=shot.camera_motion,
                duration_sec=final_duration,
            ),
            check=True,
        )
        clip_paths.append(clip_path)

    paths.subtitle_file.write_text(
        build_subtitles(shots, final_durations),
        encoding="utf-8",
    )

    concat_manifest = paths.build_dir / "concat.txt"
    concat_manifest.write_text(build_concat_manifest(clip_paths), encoding="utf-8")

    plain_video = paths.build_dir / "episode-001-plain.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_manifest),
            "-c",
            "copy",
            str(plain_video),
        ],
        check=True,
    )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(plain_video),
            "-vf",
            f"subtitles={paths.subtitle_file}",
            "-c:v",
            "libx264",
            "-c:a",
            "copy",
            str(paths.render_output),
        ],
        check=True,
    )

    return paths.render_output


def parse_args() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("--project", default="demo-001")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
    )
    return parser


def main() -> None:
    args = parse_args().parse_args()
    paths = ProjectPaths(repo_root=Path(args.repo_root), project_name=args.project)
    output_path = render_project_video(paths)
    print(f"Rendered final video: {output_path}")


if __name__ == "__main__":
    main()
