#!/usr/bin/env python3
from argparse import ArgumentParser
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.local_video.assets import select_candidate
from scripts.local_video.project_paths import ProjectPaths


def select_project_still(
    paths: ProjectPaths,
    shot_id: str,
    candidate_path: Path,
    status: str,
    notes: str,
) -> Path:
    return select_candidate(
        paths=paths,
        shot_id=shot_id,
        candidate_path=candidate_path,
        status=status,
        notes=notes,
    )


def parse_args() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("--project", default="demo-001")
    parser.add_argument("--shot", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--status", default="accepted")
    parser.add_argument("--notes", default="")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
    )
    return parser


def main() -> None:
    args = parse_args().parse_args()
    paths = ProjectPaths(repo_root=Path(args.repo_root), project_name=args.project)
    output_path = select_project_still(
        paths=paths,
        shot_id=args.shot,
        candidate_path=Path(args.candidate),
        status=args.status,
        notes=args.notes,
    )
    print(f"Selected still: {output_path}")


if __name__ == "__main__":
    main()
