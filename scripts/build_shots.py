#!/usr/bin/env python3
from argparse import ArgumentParser
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.local_video.project_paths import ProjectPaths
from scripts.local_video.shots import Shot, dump_shots, load_shots


def normalize_project_shots(paths: ProjectPaths) -> int:
    if not paths.story_file.exists():
        raise FileNotFoundError(f"Missing story.md: {paths.story_file}")
    if not paths.shots_file.exists():
        raise FileNotFoundError(f"Missing shots.json: {paths.shots_file}")

    shots = load_shots(paths.shots_file)
    normalized: list[Shot] = []
    for shot in shots:
        image_ref = Path(shot.image)
        if image_ref.is_absolute():
            raise ValueError(f"Shot image must be project-relative: {shot.image}")
        image_path = paths.project_dir / image_ref
        if not image_path.exists():
            raise FileNotFoundError(f"Missing still image: {image_path}")

        normalized.append(
            Shot(
                id=shot.id,
                image=image_path.relative_to(paths.project_dir).as_posix(),
                duration_sec=shot.duration_sec,
                camera_motion=shot.camera_motion,
                voice=shot.voice,
                dialogue=shot.dialogue.strip(),
                subtitle=shot.subtitle.strip(),
            )
        )

    dump_shots(paths.shots_file, normalized)
    return len(normalized)


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
    count = normalize_project_shots(paths)
    print(f"Normalized {count} shots for {args.project}")


if __name__ == "__main__":
    main()
