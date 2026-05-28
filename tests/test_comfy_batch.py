from pathlib import Path

import pytest

from scripts.local_video.assets import import_candidate
from scripts.local_video.comfy_batch import (
    DEFAULT_VARIANT_SEED_STEP,
    ShotBatchSummary,
    generate_candidates_for_project,
    generate_candidates_for_shot,
)
from scripts.local_video.comfyui import ComfyUITransientError
from scripts.local_video.project_paths import ProjectPaths
from scripts.local_video.shots import Shot, dump_shots


def test_generate_candidates_for_shot_retries_until_variants_are_filled(tmp_path: Path) -> None:
    paths = ProjectPaths(repo_root=tmp_path, project_name="demo-001")
    paths.prompts_dir.mkdir(parents=True)
    (paths.prompts_dir / "shot-001.md").write_text(
        "## Global Style\n\nvertical manhua",
        encoding="utf-8",
    )

    calls: list[tuple[str, int, str]] = []
    failures = iter([ComfyUITransientError("temporary"), None, None])

    def fake_generate_one(**kwargs) -> Path:
        calls.append((kwargs["shot_id"], kwargs["seed"], kwargs["variant_name"]))
        result = next(failures)
        if result is not None:
            raise result
        output = tmp_path / f"{len(calls)}.png"
        output.write_bytes(b"image")
        return import_candidate(
            paths=kwargs["paths"],
            shot_id=kwargs["shot_id"],
            source_image=output,
            source="comfyui",
            notes=f"seed {kwargs['seed']}",
        )

    summary = generate_candidates_for_shot(
        paths=paths,
        shot_id="shot-001",
        client=object(),
        variants=2,
        max_attempts_per_image=20,
        generate_one=fake_generate_one,
    )

    assert len(summary.created_paths) == 2
    assert summary.retries_used == 1
    assert [shot_id for shot_id, _, _ in calls] == ["shot-001", "shot-001", "shot-001"]
    assert calls[-2][1] == 527003
    assert calls[-1][1] == 527002 + DEFAULT_VARIANT_SEED_STEP + 1
    assert [variant_name for _, _, variant_name in calls[-2:]] == ["portrait", "environment"]


def test_generate_candidates_for_project_waits_for_current_shot_before_next(tmp_path: Path) -> None:
    paths = ProjectPaths(repo_root=tmp_path, project_name="demo-001")
    paths.project_dir.mkdir(parents=True)
    dump_shots(
        paths.shots_file,
        [
            Shot(
                id="shot-001",
                image="stills/shot-001.png",
                duration_sec=1.0,
                camera_motion="static",
                voice="narrator",
                dialogue="a",
                subtitle="a",
            ),
            Shot(
                id="shot-002",
                image="stills/shot-002.png",
                duration_sec=1.0,
                camera_motion="static",
                voice="narrator",
                dialogue="b",
                subtitle="b",
            ),
        ],
    )
    order: list[str] = []

    def fake_generate_shot(**kwargs) -> ShotBatchSummary:
        order.append(kwargs["shot_id"])
        return ShotBatchSummary(
            shot_id=kwargs["shot_id"],
            created_paths=[],
            retries_used=0,
        )

    generate_candidates_for_project(
        paths=paths,
        client=object(),
        variants=2,
        generate_shot=fake_generate_shot,
    )

    assert order == ["shot-001", "shot-002"]


def test_generate_candidates_for_shot_stops_on_missing_prompt(tmp_path: Path) -> None:
    paths = ProjectPaths(repo_root=tmp_path, project_name="demo-001")

    with pytest.raises(FileNotFoundError, match="Missing prompt file"):
        generate_candidates_for_shot(
            paths=paths,
            shot_id="shot-001",
            client=object(),
            variants=2,
        )
