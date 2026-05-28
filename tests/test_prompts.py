from pathlib import Path

from scripts.local_video.project_paths import ProjectPaths
from scripts.local_video.prompts import (
    CharacterAnchor,
    select_character_anchors_for_shot,
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
        model_visual_prompt="young woman waking in a ruined cold palace bedchamber, moonlight across her shocked face",
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
    assert "young woman waking in a ruined cold palace bedchamber" in prompt
    assert "Only include characters described in the shot composition" in prompt
    assert "no modern clothing" in prompt


def test_select_character_anchors_for_shot_returns_only_relevant_anchors() -> None:
    shot = Shot(
        id="shot-001",
        image="stills/shot-001.png",
        duration_sec=6.0,
        camera_motion="slow_push_in",
        voice="female_narrator",
        dialogue="我不是应该死在手术台上吗？",
        subtitle="我不是应该死在手术台上吗？",
        visual_prompt="苏晚在冷宫榻上惊醒，月光照在脸上。",
        model_visual_prompt="young woman waking up in moonlight",
        negative_prompt="no modern clothing",
    )
    anchors = [
        CharacterAnchor(
            id="su_wan",
            name="苏晚",
            role="穿越女主",
            prompt="young woman in pale blue hanfu",
            continuity="same face",
        ),
        CharacterAnchor(
            id="regent_prince",
            name="萧景珩",
            role="摄政王",
            prompt="tall Chinese man in black robe",
            continuity="same crown",
        ),
        CharacterAnchor(
            id="system_panel",
            name="系统面板",
            role="系统 UI",
            prompt="floating translucent golden system interface",
            continuity="same gold geometry",
        ),
    ]

    selected = select_character_anchors_for_shot(shot, anchors)

    assert [anchor.id for anchor in selected] == ["su_wan"]


def test_select_character_anchors_for_shot_uses_model_visual_prompt_when_present() -> None:
    shot = Shot(
        id="shot-001",
        image="stills/shot-001.png",
        duration_sec=6.0,
        camera_motion="slow_push_in",
        voice="female_narrator",
        dialogue="旁白",
        subtitle="旁白",
        visual_prompt="一名女子醒来。",
        model_visual_prompt="the regent prince steps out from the corridor shadows",
        negative_prompt="no modern clothing",
    )
    anchors = [
        CharacterAnchor(
            id="su_wan",
            name="苏晚",
            role="穿越女主",
            prompt="young woman in pale blue hanfu",
            continuity="same face",
        ),
        CharacterAnchor(
            id="regent_prince",
            name="萧景珩",
            role="regent prince",
            prompt="tall Chinese man in black robe",
            continuity="same crown",
        ),
    ]

    selected = select_character_anchors_for_shot(shot, anchors)

    assert [anchor.id for anchor in selected] == ["regent_prince"]


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
          },
          {
            "id": "regent_prince",
            "name": "萧景珩",
            "role": "摄政王",
            "prompt": "tall Chinese man in black robe",
            "continuity": "same crown"
          },
          {
            "id": "system_panel",
            "name": "系统面板",
            "role": "系统 UI",
            "prompt": "floating translucent golden system interface",
            "continuity": "same gold geometry"
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
                model_visual_prompt="young woman waking up inside a ruined cold palace room",
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
    shot_one_text = written[0].read_text(encoding="utf-8")
    shot_two_text = written[1].read_text(encoding="utf-8")
    assert "冷宫惊醒" in shot_one_text
    assert "young woman waking up inside a ruined cold palace room" in shot_one_text
    assert "金色系统面板" in shot_two_text
    assert "苏晚" in shot_one_text
    assert "萧景珩" not in shot_one_text
    assert "系统面板" not in shot_one_text
