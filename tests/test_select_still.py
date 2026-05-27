from pathlib import Path

from scripts.local_video.assets import import_candidate
from scripts.local_video.project_paths import ProjectPaths
from scripts.select_still import select_project_still


def test_select_project_still_returns_final_still_path(tmp_path: Path) -> None:
    paths = ProjectPaths(repo_root=tmp_path, project_name="demo-001")
    source_image = tmp_path / "local.png"
    source_image.write_bytes(b"selected image")
    imported = import_candidate(
        paths=paths,
        shot_id="shot-001",
        source_image=source_image,
        source="local",
        notes="first local pass",
    )

    final_still = select_project_still(
        paths=paths,
        shot_id="shot-001",
        candidate_path=imported,
        status="accepted",
        notes="use local image",
    )

    assert final_still == paths.stills_dir / "shot-001.png"
    assert final_still.read_bytes() == b"selected image"
