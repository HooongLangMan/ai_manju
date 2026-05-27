#!/usr/bin/env python3
from argparse import ArgumentParser
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.local_video.assets import import_candidate
from scripts.local_video.project_paths import ProjectPaths


def import_project_candidate(
    paths: ProjectPaths,
    shot_id: str,
    source_image: Path,
    source: str,
    notes: str,
) -> Path:
    return import_candidate(
        paths=paths,
        shot_id=shot_id,
        source_image=source_image,
        source=source,
        notes=notes,
    )


def parse_args() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("--project", default="demo-001")
    parser.add_argument("--shot", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--source", default="local")
    parser.add_argument("--notes", default="")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
    )
    return parser


def main() -> None:
    args = parse_args().parse_args()
    paths = ProjectPaths(repo_root=Path(args.repo_root), project_name=args.project)
    output_path = import_project_candidate(
        paths=paths,
        shot_id=args.shot,
        source_image=Path(args.image),
        source=args.source,
        notes=args.notes,
    )
    print(f"Imported candidate: {output_path}")


if __name__ == "__main__":
    main()
