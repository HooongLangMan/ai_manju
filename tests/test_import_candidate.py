from pathlib import Path

from scripts.import_candidate import import_project_candidate
from scripts.local_video.project_paths import ProjectPaths


def test_import_project_candidate_returns_candidate_path(tmp_path: Path) -> None:
    paths = ProjectPaths(repo_root=tmp_path, project_name="demo-001")
    source_image = tmp_path / "local.png"
    source_image.write_bytes(b"local image")

    imported = import_project_candidate(
        paths=paths,
        shot_id="shot-001",
        source_image=source_image,
        source="local",
        notes="first local pass",
    )

    assert imported == paths.candidates_dir / "shot-001" / "local-001.png"
    assert imported.read_bytes() == b"local image"
