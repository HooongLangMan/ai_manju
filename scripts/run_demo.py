#!/usr/bin/env python3
from argparse import ArgumentParser
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.build_audio import build_project_audio
from scripts.build_shots import normalize_project_shots
from scripts.local_video.project_paths import ProjectPaths
from scripts.render_video import render_project_video


def run_pipeline(paths: ProjectPaths) -> Path:
    normalize_project_shots(paths)
    build_project_audio(paths)
    return render_project_video(paths)


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
    output_path = run_pipeline(paths)
    print(f"Finished demo render: {output_path}")


if __name__ == "__main__":
    main()
