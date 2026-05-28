from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from scripts.local_video.assets import import_candidate, remove_candidates_by_source
from scripts.local_video.comfyui import (
    ComfyUIClient,
    ComfyUITransientError,
    build_flux_schnell_prompt,
    project_prompt_to_flux_negative_text,
    project_prompt_to_flux_text,
)
from scripts.local_video.project_paths import ProjectPaths
from scripts.local_video.shots import load_shots


@dataclass(frozen=True)
class ShotBatchSummary:
    shot_id: str
    created_paths: list[Path]
    retries_used: int


@dataclass(frozen=True)
class BatchRunSummary:
    mode: str
    shot_summaries: list[ShotBatchSummary]
    replace_source: str | None


DEFAULT_VARIANT_SEQUENCE = ["portrait", "medium", "environment"]
DEFAULT_VARIANT_SEED_STEP = 97


def generate_shot_candidate(
    paths: ProjectPaths,
    shot_id: str,
    client: ComfyUIClient,
    checkpoint_name: str,
    width: int,
    height: int,
    seed: int,
    steps: int,
    cfg: float,
    variant_name: str,
) -> Path:
    prompt_path = paths.prompts_dir / f"{shot_id}.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Missing prompt file: {prompt_path}")
    prompt_markdown = prompt_path.read_text(encoding="utf-8")
    prompt_text = project_prompt_to_flux_text(
        prompt_markdown,
        variant_name=variant_name,
    )
    negative_text = project_prompt_to_flux_negative_text(prompt_markdown)
    workflow = build_flux_schnell_prompt(
        text=prompt_text,
        negative_text=negative_text,
        checkpoint_name=checkpoint_name,
        width=width,
        height=height,
        seed=seed,
        steps=steps,
        cfg=cfg,
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


def generate_candidates_for_shot(
    paths: ProjectPaths,
    shot_id: str,
    client: ComfyUIClient,
    variants: int,
    replace_source: str | None = None,
    checkpoint_name: str = "flux1-schnell-fp8.safetensors",
    width: int = 576,
    height: int = 1024,
    seed: int = 527002,
    steps: int = 8,
    cfg: float = 2.5,
    max_attempts_per_image: int = 20,
    generate_one: Callable | None = None,
) -> ShotBatchSummary:
    generator = generate_one or generate_shot_candidate
    prompt_path = paths.prompts_dir / f"{shot_id}.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Missing prompt file: {prompt_path}")
    if replace_source == "comfyui":
        remove_candidates_by_source(paths, shot_id, "comfyui")

    created: list[Path] = []
    retries_used = 0
    for slot_index in range(variants):
        attempts = 0
        variant_name = DEFAULT_VARIANT_SEQUENCE[
            slot_index % len(DEFAULT_VARIANT_SEQUENCE)
        ]
        while True:
            attempts += 1
            current_seed = seed + slot_index * DEFAULT_VARIANT_SEED_STEP + retries_used
            try:
                created.append(
                    generator(
                        paths=paths,
                        shot_id=shot_id,
                        client=client,
                        checkpoint_name=checkpoint_name,
                        width=width,
                        height=height,
                        seed=current_seed,
                        steps=steps,
                        cfg=cfg,
                        variant_name=variant_name,
                    )
                )
                break
            except ComfyUITransientError:
                retries_used += 1
                if attempts >= max_attempts_per_image:
                    raise

    return ShotBatchSummary(
        shot_id=shot_id,
        created_paths=created,
        retries_used=retries_used,
    )


def generate_candidates_for_project(
    paths: ProjectPaths,
    client: ComfyUIClient,
    variants: int,
    replace_source: str | None = None,
    checkpoint_name: str = "flux1-schnell-fp8.safetensors",
    width: int = 576,
    height: int = 1024,
    seed: int = 527002,
    steps: int = 8,
    cfg: float = 2.5,
    max_attempts_per_image: int = 20,
    generate_shot: Callable | None = None,
) -> BatchRunSummary:
    shots = load_shots(paths.shots_file)
    generator = generate_shot or generate_candidates_for_shot
    summaries = [
        generator(
            paths=paths,
            shot_id=shot.id,
            client=client,
            variants=variants,
            replace_source=replace_source,
            checkpoint_name=checkpoint_name,
            width=width,
            height=height,
            seed=seed + index * 1000,
            steps=steps,
            cfg=cfg,
            max_attempts_per_image=max_attempts_per_image,
        )
        for index, shot in enumerate(shots)
    ]
    return BatchRunSummary(
        mode="project",
        shot_summaries=summaries,
        replace_source=replace_source,
    )
