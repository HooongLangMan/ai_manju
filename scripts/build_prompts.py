#!/usr/bin/env python3
from argparse import ArgumentParser
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.local_video.project_paths import ProjectPaths
from scripts.local_video.prompts import write_project_prompts


def build_project_prompts(paths: ProjectPaths) -> int:
    return len(write_project_prompts(paths))


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
    count = build_project_prompts(paths)
    print(f"Wrote {count} prompt files to {paths.prompts_dir}")


if __name__ == "__main__":
    main()
