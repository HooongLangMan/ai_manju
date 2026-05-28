#!/usr/bin/env python3
from argparse import ArgumentParser, Namespace
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.local_video.comfy_batch import (
    BatchRunSummary,
    ShotBatchSummary,
    generate_candidates_for_project,
    generate_candidates_for_shot,
)
from scripts.local_video.comfyui import ComfyUIClient
from scripts.local_video.project_paths import ProjectPaths


def generate_project_candidate(
    paths: ProjectPaths,
    shot_id: str,
    client: ComfyUIClient,
    checkpoint_name: str = "flux1-schnell-fp8.safetensors",
    width: int = 576,
    height: int = 1024,
    seed: int = 527002,
    steps: int = 4,
) -> Path:
    summary = generate_candidates_for_shot(
        paths=paths,
        shot_id=shot_id,
        client=client,
        variants=1,
        checkpoint_name=checkpoint_name,
        width=width,
        height=height,
        seed=seed,
        steps=steps,
    )
    return summary.created_paths[0]


def parse_args() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("--project", default="demo-001")
    parser.add_argument("--shot")
    parser.add_argument("--variants", type=int, default=2)
    parser.add_argument("--replace-source", choices=["comfyui"])
    parser.add_argument("--max-attempts-per-image", type=int, default=20)
    parser.add_argument("--base-url", default="http://127.0.0.1:8188")
    parser.add_argument(
        "--output-dir",
        default="/Users/kelton/ai漫剧/ComfyUI/output",
    )
    parser.add_argument("--checkpoint", default="flux1-schnell-fp8.safetensors")
    parser.add_argument("--width", type=int, default=576)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--seed", type=int, default=527002)
    parser.add_argument("--steps", type=int, default=4)
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
    )
    return parser


def run_generation(args: Namespace) -> BatchRunSummary | ShotBatchSummary:
    paths = ProjectPaths(repo_root=Path(args.repo_root), project_name=args.project)
    client = ComfyUIClient(
        base_url=args.base_url,
        output_dir=Path(args.output_dir),
    )
    if args.shot:
        return generate_candidates_for_shot(
            paths=paths,
            shot_id=args.shot,
            client=client,
            variants=args.variants,
            replace_source=args.replace_source,
            checkpoint_name=args.checkpoint,
            width=args.width,
            height=args.height,
            seed=args.seed,
            steps=args.steps,
            max_attempts_per_image=args.max_attempts_per_image,
        )
    return generate_candidates_for_project(
        paths=paths,
        client=client,
        variants=args.variants,
        replace_source=args.replace_source,
        checkpoint_name=args.checkpoint,
        width=args.width,
        height=args.height,
        seed=args.seed,
        steps=args.steps,
        max_attempts_per_image=args.max_attempts_per_image,
    )


def _format_summary(summary: BatchRunSummary | ShotBatchSummary, project: str) -> str:
    if isinstance(summary, ShotBatchSummary):
        return (
            f"Project {project}: generated {len(summary.created_paths)} image(s) "
            f"for {summary.shot_id} with {summary.retries_used} retrie(s)"
        )

    images_created = sum(len(item.created_paths) for item in summary.shot_summaries)
    retries_used = sum(item.retries_used for item in summary.shot_summaries)
    return (
        f"Project {project}: processed {len(summary.shot_summaries)} shot(s), "
        f"generated {images_created} image(s), retries used {retries_used}, "
        f"replace_source={summary.replace_source or 'append'}"
    )


def main() -> None:
    args = parse_args().parse_args()
    summary = run_generation(args)
    print(_format_summary(summary, args.project))


if __name__ == "__main__":
    main()
