import json
from pathlib import Path

import pytest

from scripts.build_shots import normalize_project_shots
from scripts.local_video.project_paths import ProjectPaths


def write_story(project_dir: Path) -> None:
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "story.md").write_text("# demo\n", encoding="utf-8")


def test_normalize_project_shots_requires_shots_json(tmp_path: Path) -> None:
    project_dir = tmp_path / "storage" / "projects" / "demo-001"
    write_story(project_dir)
    paths = ProjectPaths(repo_root=tmp_path, project_name="demo-001")

    with pytest.raises(FileNotFoundError, match="shots.json"):
        normalize_project_shots(paths)


def test_normalize_project_shots_requires_existing_image_files(tmp_path: Path) -> None:
    project_dir = tmp_path / "storage" / "projects" / "demo-001"
    (project_dir / "stills").mkdir(parents=True, exist_ok=True)
    write_story(project_dir)
    (project_dir / "shots.json").write_text(
        json.dumps(
            [
                {
                    "id": "shot-001",
                    "image": "stills/missing.png",
                    "duration_sec": 6,
                    "camera_motion": "static",
                    "voice": "female_narrator",
                    "dialogue": "你好",
                    "subtitle": "你好",
                }
            ]
        ),
        encoding="utf-8",
    )
    paths = ProjectPaths(repo_root=tmp_path, project_name="demo-001")

    with pytest.raises(FileNotFoundError, match="missing.png"):
        normalize_project_shots(paths)
