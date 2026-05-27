from pathlib import Path

from scripts.build_prompts import build_project_prompts
from scripts.local_video.project_paths import ProjectPaths
from scripts.local_video.shots import Shot, dump_shots


def test_build_project_prompts_returns_written_count(tmp_path: Path) -> None:
    paths = ProjectPaths(repo_root=tmp_path, project_name="demo-001")
    paths.project_dir.mkdir(parents=True)
    paths.characters_file.write_text(
        """
        [
          {
            "id": "su_wan",
            "name": "苏晚",
            "role": "穿越女主",
            "prompt": "young woman in pale blue hanfu",
            "continuity": "same face"
          }
        ]
        """.strip(),
        encoding="utf-8",
    )
    paths.style_guide_file.write_text("vertical manhua palace style", encoding="utf-8")
    dump_shots(
        paths.shots_file,
        [
            Shot(
                id="shot-001",
                image="stills/shot-001.png",
                duration_sec=6.0,
                camera_motion="slow_push_in",
                voice="female_narrator",
                dialogue="你好",
                subtitle="你好",
                visual_prompt="冷宫惊醒。",
            )
        ],
    )

    count = build_project_prompts(paths)

    assert count == 1
    assert (paths.prompts_dir / "shot-001.md").exists()
