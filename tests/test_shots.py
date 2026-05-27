from pathlib import Path

import pytest

from scripts.local_video.project_paths import ProjectPaths
from scripts.local_video.shots import Shot, dump_shots, load_shots


def test_project_paths_point_to_demo_directories(tmp_path: Path) -> None:
    paths = ProjectPaths(repo_root=tmp_path, project_name="demo-001")

    assert paths.project_dir == tmp_path / "storage" / "projects" / "demo-001"
    assert paths.story_file == paths.project_dir / "story.md"
    assert paths.audio_dir == paths.project_dir / "audio"
    assert paths.subtitle_file == paths.build_dir / "subtitles.srt"
    assert paths.render_output == tmp_path / "storage" / "renders" / "episode-001.mp4"


def test_load_shots_rejects_unknown_camera_motion(tmp_path: Path) -> None:
    payload = """
    [
      {
        "id": "shot-001",
        "image": "stills/shot-001.png",
        "duration_sec": 6,
        "camera_motion": "spin",
        "voice": "female_narrator",
        "dialogue": "你好",
        "subtitle": "你好"
      }
    ]
    """.strip()
    shots_file = tmp_path / "shots.json"
    shots_file.write_text(payload, encoding="utf-8")

    with pytest.raises(ValueError, match="camera_motion"):
        load_shots(shots_file)


def test_dump_shots_round_trips(tmp_path: Path) -> None:
    shot = Shot(
        id="shot-001",
        image="stills/shot-001.png",
        duration_sec=6.0,
        camera_motion="slow_push_in",
        voice="female_narrator",
        dialogue="我回来了。",
        subtitle="我回来了。",
    )
    shots_file = tmp_path / "shots.json"

    dump_shots(shots_file, [shot])

    assert load_shots(shots_file) == [shot]
