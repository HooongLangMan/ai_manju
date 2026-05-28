import json
from pathlib import Path

import pytest

from scripts.local_video.assets import (
    import_candidate,
    load_asset_manifest,
    remove_candidates_by_source,
    select_candidate,
)
from scripts.local_video.project_paths import ProjectPaths


def test_load_asset_manifest_returns_empty_dict_when_missing(tmp_path: Path) -> None:
    paths = ProjectPaths(repo_root=tmp_path, project_name="demo-001")

    assert load_asset_manifest(paths) == {}


def test_import_candidate_copies_image_and_records_manifest(tmp_path: Path) -> None:
    paths = ProjectPaths(repo_root=tmp_path, project_name="demo-001")
    source = tmp_path / "source.png"
    source.write_bytes(b"candidate image")

    imported = import_candidate(
        paths=paths,
        shot_id="shot-001",
        source_image=source,
        source="local",
        notes="ComfyUI first pass",
    )

    assert imported == paths.candidates_dir / "shot-001" / "local-001.png"
    assert imported.read_bytes() == b"candidate image"
    manifest = json.loads(paths.asset_manifest_file.read_text(encoding="utf-8"))
    assert manifest["shot-001"]["candidates"] == [
        {
            "path": "candidates/shot-001/local-001.png",
            "source": "local",
            "notes": "ComfyUI first pass",
        }
    ]
    assert not (paths.stills_dir / "shot-001.png").exists()


def test_import_candidate_increments_names_per_source(tmp_path: Path) -> None:
    paths = ProjectPaths(repo_root=tmp_path, project_name="demo-001")
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    first.write_bytes(b"first")
    second.write_bytes(b"second")

    import_candidate(paths, "shot-001", first, source="local", notes="")
    imported = import_candidate(paths, "shot-001", second, source="local", notes="")

    assert imported == paths.candidates_dir / "shot-001" / "local-002.png"


def test_select_candidate_copies_candidate_to_final_still(tmp_path: Path) -> None:
    paths = ProjectPaths(repo_root=tmp_path, project_name="demo-001")
    source = tmp_path / "source.png"
    source.write_bytes(b"chosen image")
    imported = import_candidate(
        paths=paths,
        shot_id="shot-001",
        source_image=source,
        source="local",
        notes="good enough locally",
    )

    final_still = select_candidate(
        paths=paths,
        shot_id="shot-001",
        candidate_path=imported,
        status="accepted",
        notes="本地图可用，不走 API",
    )

    assert final_still == paths.stills_dir / "shot-001.png"
    assert final_still.read_bytes() == b"chosen image"
    manifest = json.loads(paths.asset_manifest_file.read_text(encoding="utf-8"))
    assert manifest["shot-001"]["selected"] == "candidates/shot-001/local-001.png"
    assert manifest["shot-001"]["status"] == "accepted"
    assert manifest["shot-001"]["notes"] == "本地图可用，不走 API"


def test_select_candidate_rejects_candidate_from_another_shot(tmp_path: Path) -> None:
    paths = ProjectPaths(repo_root=tmp_path, project_name="demo-001")
    source = tmp_path / "source.png"
    source.write_bytes(b"wrong shot")
    imported = import_candidate(paths, "shot-002", source, source="local", notes="")

    with pytest.raises(ValueError, match="does not belong to shot-001"):
        select_candidate(paths, "shot-001", imported, status="accepted", notes="")


def test_remove_candidates_by_source_only_removes_matching_source(tmp_path: Path) -> None:
    paths = ProjectPaths(repo_root=tmp_path, project_name="demo-001")
    comfy_source = tmp_path / "comfy.png"
    local_source = tmp_path / "local.png"
    comfy_source.write_bytes(b"comfy")
    local_source.write_bytes(b"local")

    comfy_imported = import_candidate(
        paths=paths,
        shot_id="shot-001",
        source_image=comfy_source,
        source="comfyui",
        notes="remove me",
    )
    local_imported = import_candidate(
        paths=paths,
        shot_id="shot-001",
        source_image=local_source,
        source="local",
        notes="keep me",
    )

    removed = remove_candidates_by_source(paths, "shot-001", "comfyui")

    assert removed == [comfy_imported]
    assert not comfy_imported.exists()
    assert local_imported.exists()
    manifest = json.loads(paths.asset_manifest_file.read_text(encoding="utf-8"))
    assert manifest["shot-001"]["candidates"] == [
        {
            "path": "candidates/shot-001/local-001.png",
            "source": "local",
            "notes": "keep me",
        }
    ]
