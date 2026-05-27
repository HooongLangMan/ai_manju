#!/usr/bin/env python3
from argparse import ArgumentParser
from pathlib import Path

from scripts.local_video.audio_builder import build_project_audio
from scripts.local_video.project_paths import ProjectPaths


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
    durations = build_project_audio(paths)
    print(f"Generated audio for {len(durations)} shots")


if __name__ == "__main__":
    main()
