#!/usr/bin/env python3
from argparse import ArgumentParser
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.local_video.assets import import_candidate
from scripts.local_video.comfyui import (
    ComfyUIClient,
    build_flux_schnell_prompt,
    project_prompt_to_flux_text,
)
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
    prompt_path = paths.prompts_dir / f"{shot_id}.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Missing prompt file: {prompt_path}")

    prompt_text = project_prompt_to_flux_text(prompt_path.read_text(encoding="utf-8"))
    workflow = build_flux_schnell_prompt(
        text=prompt_text,
        checkpoint_name=checkpoint_name,
        width=width,
        height=height,
        seed=seed,
        steps=steps,
        filename_prefix=f"ai_manga_{paths.project_name}_{shot_id}_flux_schnell",
    )
    prompt_id = client.queue_prompt(workflow)
    outputs = client.wait_for_output_images(prompt_id)
    output_image = client.output_image_path(outputs[0])
    return import_candidate(
        paths=paths,
        shot_id=shot_id,
        source_image=output_image,
        source="comfyui",
        notes=f"ComfyUI {checkpoint_name}, seed {seed}, {width}x{height}, {steps} steps",
    )


def parse_args() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("--project", default="demo-001")
    parser.add_argument("--shot", required=True)
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


def main() -> None:
    args = parse_args().parse_args()
    paths = ProjectPaths(repo_root=Path(args.repo_root), project_name=args.project)
    client = ComfyUIClient(
        base_url=args.base_url,
        output_dir=Path(args.output_dir),
    )
    output_path = generate_project_candidate(
        paths=paths,
        shot_id=args.shot,
        client=client,
        checkpoint_name=args.checkpoint,
        width=args.width,
        height=args.height,
        seed=args.seed,
        steps=args.steps,
    )
    print(f"Imported ComfyUI candidate: {output_path}")


if __name__ == "__main__":
    main()
