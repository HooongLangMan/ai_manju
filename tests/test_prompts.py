from pathlib import Path

from scripts.local_video.project_paths import ProjectPaths
from scripts.local_video.prompts import (
    CharacterAnchor,
    load_character_anchors,
    render_shot_prompt,
    write_project_prompts,
)
from scripts.local_video.shots import Shot, dump_shots


def test_load_character_anchors_reads_named_anchors(tmp_path: Path) -> None:
    characters_file = tmp_path / "characters.json"
    characters_file.write_text(
        """
        [
          {
            "id": "su_wan",
            "name": "苏晚",
            "role": "穿越女主",
            "prompt": "young woman in pale blue hanfu",
            "continuity": "keep the same face and costume"
          }
        ]
        """.strip(),
        encoding="utf-8",
    )

    anchors = load_character_anchors(characters_file)

    assert anchors == [
        CharacterAnchor(
            id="su_wan",
            name="苏晚",
            role="穿越女主",
            prompt="young woman in pale blue hanfu",
            continuity="keep the same face and costume",
        )
    ]


def test_render_shot_prompt_includes_style_characters_and_shot_details() -> None:
    shot = Shot(
        id="shot-001",
        image="stills/shot-001.png",
        duration_sec=6.0,
        camera_motion="slow_push_in",
        voice="female_narrator",
        dialogue="我不是应该死在手术台上吗？",
        subtitle="我不是应该死在手术台上吗？",
        visual_prompt="苏晚在冷宫榻上惊醒，月光照在脸上。",
        negative_prompt="no modern clothing",
    )
    anchors = [
        CharacterAnchor(
            id="su_wan",
            name="苏晚",
            role="穿越女主",
            prompt="young woman in pale blue hanfu",
            continuity="same face, same hair ornament",
        )
    ]

    prompt = render_shot_prompt(
        shot=shot,
        style_guide="vertical 9:16 cinematic manhua, cold palace moonlight",
        character_anchors=anchors,
    )

    assert "# shot-001" in prompt
    assert "vertical 9:16 cinematic manhua" in prompt
    assert "苏晚" in prompt
    assert "young woman in pale blue hanfu" in prompt
    assert "苏晚在冷宫榻上惊醒" in prompt
    assert "Only include characters described in the shot composition" in prompt
    assert "no modern clothing" in prompt


def test_write_project_prompts_writes_one_markdown_file_per_shot(tmp_path: Path) -> None:
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
    paths.style_guide_file.write_text(
        "vertical 9:16 cinematic manhua, ancient palace",
        encoding="utf-8",
    )
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
                negative_prompt="low quality",
            ),
            Shot(
                id="shot-002",
                image="stills/shot-002.png",
                duration_sec=5.0,
                camera_motion="static",
                voice="system_voice",
                dialogue="系统提示",
                subtitle="系统提示",
                visual_prompt="金色系统面板浮现。",
                negative_prompt="watermark",
            ),
        ],
    )

    written = write_project_prompts(paths)

    assert written == [
        paths.prompts_dir / "shot-001.md",
        paths.prompts_dir / "shot-002.md",
    ]
    assert "冷宫惊醒" in written[0].read_text(encoding="utf-8")
    assert "金色系统面板" in written[1].read_text(encoding="utf-8")
