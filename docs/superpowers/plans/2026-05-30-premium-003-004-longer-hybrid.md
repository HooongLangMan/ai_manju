# Premium 003/004 Longer Hybrid Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade `premium-003-004` from the short three-shot premium sample into a longer 24-30 second hybrid validation sample with five shots, better external voices, motion templates matched to shot purpose, and review-friendly render outputs.

**Architecture:** Keep the existing still-generation and render pipeline, but extend the shot schema so each shot explicitly carries `voice_type`, `action_goal`, and `motion_intent`. Add a switchable audio provider layer with an `edge-tts` path plus silent-shot handling, then make the Wan I2V and render stages read the richer shot intent instead of treating every shot as the same animated card.

**Tech Stack:** Python CLI scripts, pytest, local JSON/Markdown project assets, `edge-tts`, ComfyUI Wan 2.2 I2V, ffmpeg/ffprobe, existing project manifest and render helpers

---

## File Map

**Project content**
- Modify: `storage/projects/premium-003-004/story.md`
- Modify: `storage/projects/premium-003-004/style_guide.md`
- Modify: `storage/projects/premium-003-004/characters.json`
- Modify: `storage/projects/premium-003-004/shots.json`

**Shot schema and prompt generation**
- Modify: `scripts/local_video/shots.py`
- Modify: `scripts/build_shots.py`
- Modify: `scripts/local_video/prompts.py`
- Modify: `scripts/build_prompts.py`
- Modify: `scripts/generate_api_stills.py`

**Audio**
- Modify: `scripts/local_video/audio_builder.py`
- Modify: `scripts/build_audio.py`
- Modify: `.env.example`

**Render and motion**
- Modify: `scripts/local_video/project_paths.py`
- Modify: `scripts/local_video/rendering.py`
- Modify: `scripts/wan22_i2v_generate.py`
- Modify: `scripts/render_video.py`
- Modify: `scripts/run_demo.py`

**Tests**
- Modify: `tests/test_premium_sample_project.py`
- Modify: `tests/test_shots.py`
- Modify: `tests/test_build_shots.py`
- Modify: `tests/test_prompts.py`
- Modify: `tests/test_build_prompts.py`
- Modify: `tests/test_generate_api_stills.py`
- Modify: `tests/test_build_audio.py`
- Modify: `tests/test_wan22_i2v_generate.py`
- Modify: `tests/test_render_video.py`
- Modify: `tests/test_run_demo.py`

---

### Task 1: Rewrite `premium-003-004` Into The Longer Five-Shot Hybrid Sample

**Files:**
- Modify: `storage/projects/premium-003-004/story.md`
- Modify: `storage/projects/premium-003-004/style_guide.md`
- Modify: `storage/projects/premium-003-004/characters.json`
- Modify: `storage/projects/premium-003-004/shots.json`
- Modify: `tests/test_premium_sample_project.py`

- [ ] **Step 1: Write the failing project-shape test**

Add to `tests/test_premium_sample_project.py`:

```python
import json
from pathlib import Path


def test_premium_sample_project_uses_longer_hybrid_shape() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    shots_file = (
        repo_root
        / "storage"
        / "projects"
        / "premium-003-004"
        / "shots.json"
    )

    shots = json.loads(shots_file.read_text(encoding="utf-8"))

    assert len(shots) == 5
    assert [shot["voice_type"] for shot in shots] == [
        "narration",
        "silent",
        "inner_voice",
        "silent",
        "spoken",
    ]
    assert sum(float(shot["duration_sec"]) for shot in shots) == 27.0
```

- [ ] **Step 2: Run the new project-shape test and verify it fails**

Run:

```bash
uv run --with pytest pytest tests/test_premium_sample_project.py::test_premium_sample_project_uses_longer_hybrid_shape -q
```

Expected: FAIL because the current `shots.json` still contains the older three-shot sample.

- [ ] **Step 3: Rewrite the premium sample project assets**

Replace `storage/projects/premium-003-004/story.md` with:

```md
# Premium 003/004 Longer Hybrid Sample

This project validates a longer, harsher quality ceiling for the premium palace-corridor beat.

The sample is intentionally long enough to expose real problems in speech, continuity, clarity, and acting feel.
```

Replace `storage/projects/premium-003-004/style_guide.md` with:

```md
Vertical 9:16 premium Chinese manhua scene frame for a palace short drama.

Visual tone: moonlit palace corridor, lacquered red pillars, deep blue-black night shadows, restrained gold accents, cold air, intimate danger.

Rendering style: semi-painted cinematic illustration, premium Chinese manhua finish, mature facial planes, restrained line accents, visible brush transitions on fabric and hair, high-status costume detail, controlled highlights, elegant negative space, clearly illustrated rather than photographic.

Medium guardrails: the image must read as a painted manhua frame, not a live-action costume-drama still, not an actress poster, not a glossy beauty campaign, and not a 3D render.

Composition rules: keep subjects readable on mobile, preserve clean lower-center subtitle space, prioritize silhouette and eye-line pressure, avoid busy props, avoid readable text in the image.

Face rules: no round egg-shaped faces, no oversized anime eyes, no childlike proportions, no soft idol-boy face, no doll-like smoothing, no cute romance-poster styling.
```

Replace `storage/projects/premium-003-004/characters.json` with:

```json
[
  {
    "id": "su_wan_premium",
    "name": "苏晚",
    "role": "穿越女主，成熟危险感版本",
    "prompt": "young Chinese woman, premium Chinese manhua heroine, glamorous sharp face, slightly elongated narrow face, mature facial planes, restrained almond eyes, elegant nose bridge, refined cheekbone-to-jaw transition, pale blue-white hanfu, intelligent dangerous gaze, semi-painted cinematic national-style manhua illustration",
    "continuity": "Keep Su Wan adult, narrow-faced, sharp, and controlled. No round face, no oversized eyes, no naive sweetness, no doll-like retouch, no live-action poster look.",
    "reference_views": {
      "front": "",
      "side": "",
      "back": ""
    }
  },
  {
    "id": "regent_prince_premium",
    "name": "萧景珩",
    "role": "摄政王，冷硬权臣版本",
    "prompt": "tall Chinese man, premium Chinese manhua male lead, cold hard minister-prince face, clear bone structure, narrow controlled eyes, severe dignity, jade crown, black robe with restrained silver embroidery, threatening composure, semi-painted cinematic national-style manhua illustration",
    "continuity": "Keep the regent prince hard, cold, and dangerous. No idol softness, no rounded cheeks, no sweet smile, no fantasy-armor redesign, no live-action poster look.",
    "reference_views": {
      "front": "",
      "side": "",
      "back": ""
    }
  }
]
```

Replace `storage/projects/premium-003-004/shots.json` with:

```json
[
  {
    "id": "shot-a",
    "image": "stills/shot-a.png",
    "duration_sec": 4.5,
    "camera_motion": "slow_pan_right",
    "voice_type": "narration",
    "voice": "female_lead",
    "dialogue": "那一瞬，她先察觉到的，不是脚步，而是逼近的压迫感。",
    "subtitle": "那一瞬，她先察觉到的，不是脚步，而是逼近的压迫感。",
    "action_goal": "宫廊里先静住，再缓慢抬眼，像被无形压力触到。",
    "motion_intent": "establishing_pressure",
    "visual_prompt": "宫廊夜色，苏晚立在红柱与阴影之间，先静后抬眼，月色压得很冷，空间感清楚，危险感先从环境进来。",
    "model_visual_prompt": "moonlit palace corridor, Su Wan standing between red pillars and deep shadow, wider medium framing, cold architectural space, subtle posture change before she slowly lifts her eyes, premium semi-painted Chinese manhua, oppressive atmosphere",
    "negative_prompt": "round face, oversized anime eyes, cute expression, soft idol styling, childish proportions, busy background, readable text, watermark, logo"
  },
  {
    "id": "shot-b",
    "image": "stills/shot-b.png",
    "duration_sec": 5.0,
    "camera_motion": "slow_push_in",
    "voice_type": "silent",
    "voice": "",
    "dialogue": "",
    "subtitle": "",
    "action_goal": "察觉后没有后退，只让呼吸和眼神微微收紧。",
    "motion_intent": "silent_reaction",
    "visual_prompt": "苏晚的反应近景，她没有开口，只在呼吸、肩颈和眼神里收紧，像在判断来人到底是威胁还是更危险的东西。",
    "model_visual_prompt": "close reaction shot of Su Wan, breath and gaze tightening, no speech, shoulder and neck tension, premium semi-painted Chinese manhua, intimate but controlled framing",
    "negative_prompt": "round face, oversized anime eyes, melodramatic crying, poster pose, readable text, watermark, logo"
  },
  {
    "id": "shot-c",
    "image": "stills/shot-c.png",
    "duration_sec": 5.0,
    "camera_motion": "static",
    "voice_type": "inner_voice",
    "voice": "female_lead",
    "dialogue": "他停得太近，近得像威胁，又像某种更危险的纵容。",
    "subtitle": "他停得太近，近得像威胁，又像某种更危险的纵容。",
    "action_goal": "在几乎没有退路的距离里重新稳住自己。",
    "motion_intent": "inner_voice_intimacy",
    "visual_prompt": "苏晚偏近景或三分之二侧脸，口部不要过分清楚，重点是她在危险距离里重新稳住自己，气息贴近但克制。",
    "model_visual_prompt": "three-quarter intimate close shot of Su Wan, mouth partially obscured, regaining composure inside dangerous proximity, premium semi-painted Chinese manhua, controlled inner tension",
    "negative_prompt": "front-facing mouth display, cheap romance poster, round face, oversized eyes, readable text, watermark, logo"
  },
  {
    "id": "shot-d",
    "image": "stills/shot-d.png",
    "duration_sec": 5.5,
    "camera_motion": "slow_pan_left",
    "voice_type": "silent",
    "voice": "",
    "dialogue": "",
    "subtitle": "",
    "action_goal": "他逼近半步，她不退，距离被压缩到越界边缘。",
    "motion_intent": "silent_relationship_pressure",
    "visual_prompt": "两人之间的压迫过渡镜头，不是站桩对视，而是距离被再次压缩，可能带到衣袖、手部、肩线、视线关系，空气像被压住。",
    "model_visual_prompt": "charged two-shot or over-shoulder transition, the regent prince closes distance by half a step while Su Wan does not retreat, compressed negative space, sleeve and hand detail, premium semi-painted Chinese manhua",
    "negative_prompt": "sweet romance poster, smiling lovers, generic embrace, round faces, busy background, readable text, watermark, logo"
  },
  {
    "id": "shot-e",
    "image": "stills/shot-e.png",
    "duration_sec": 7.0,
    "camera_motion": "slow_push_in",
    "voice_type": "spoken",
    "voice": "male_regent",
    "dialogue": "你，不是她。",
    "subtitle": "你，不是她。",
    "action_goal": "压下来，把一句话说得像拆穿，也像逼近。",
    "motion_intent": "spoken_hero",
    "visual_prompt": "摄政王压下来的英雄近景，最好是三分之二侧或带压力角度，不要平直正脸嘴型展示，台词落下后留一点停顿。",
    "model_visual_prompt": "oppressive hero close-up of the regent prince leaning into frame, pressure angle, severe gaze, dangerous intimate distance, one short spoken line, premium semi-painted Chinese manhua",
    "negative_prompt": "soft idol face, smiling expression, round cheeks, straight-on talking head, readable text, watermark, logo"
  }
]
```

- [ ] **Step 4: Run the project-shape tests**

Run:

```bash
uv run --with pytest pytest tests/test_premium_sample_project.py -q
```

Expected: PASS with both the original existence test and the new five-shot structure test green.

- [ ] **Step 5: Commit the project rewrite**

```bash
git add tests/test_premium_sample_project.py storage/projects/premium-003-004
git commit -m "feat: rewrite premium sample as longer hybrid scene"
```

### Task 2: Extend The Shot Schema For Voice Type, Action Goal, And Motion Intent

**Files:**
- Modify: `scripts/local_video/shots.py`
- Modify: `scripts/build_shots.py`
- Modify: `tests/test_shots.py`
- Modify: `tests/test_build_shots.py`

- [ ] **Step 1: Write failing schema tests**

Add to `tests/test_shots.py`:

```python
def test_load_shots_allows_silent_shot_without_voice_or_dialogue(tmp_path: Path) -> None:
    shots_file = tmp_path / "shots.json"
    shots_file.write_text(
        """
        [
          {
            "id": "shot-001",
            "image": "stills/shot-001.png",
            "duration_sec": 5,
            "camera_motion": "static",
            "voice_type": "silent",
            "voice": "",
            "dialogue": "",
            "subtitle": "",
            "action_goal": "hold position",
            "motion_intent": "silent_reaction"
          }
        ]
        """.strip(),
        encoding="utf-8",
    )

    [shot] = load_shots(shots_file)
    assert shot.voice_type == "silent"
    assert shot.voice == ""
    assert shot.motion_intent == "silent_reaction"


def test_load_shots_rejects_spoken_shot_without_voice_key(tmp_path: Path) -> None:
    shots_file = tmp_path / "shots.json"
    shots_file.write_text(
        """
        [
          {
            "id": "shot-001",
            "image": "stills/shot-001.png",
            "duration_sec": 5,
            "camera_motion": "static",
            "voice_type": "spoken",
            "voice": "",
            "dialogue": "你，不是她。",
            "subtitle": "你，不是她。",
            "action_goal": "deliver the line",
            "motion_intent": "spoken_hero"
          }
        ]
        """.strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="voice key"):
        load_shots(shots_file)
```

Add to `tests/test_build_shots.py`:

```python
def test_normalize_project_shots_trims_extended_shot_metadata(tmp_path: Path) -> None:
    project_dir = tmp_path / "storage" / "projects" / "premium-003-004"
    stills_dir = project_dir / "stills"
    stills_dir.mkdir(parents=True, exist_ok=True)
    write_story(project_dir)
    (stills_dir / "shot-a.png").write_bytes(b"fake image")
    shots_file = project_dir / "shots.json"
    shots_file.write_text(
        json.dumps(
            [
                {
                    "id": "shot-a",
                    "image": "stills/shot-a.png",
                    "duration_sec": 4.5,
                    "camera_motion": "slow_push_in",
                    "voice_type": "inner_voice",
                    "voice": " female_lead ",
                    "dialogue": " 很近。 ",
                    "subtitle": " 很近。 ",
                    "action_goal": " 重新稳住自己 ",
                    "motion_intent": " inner_voice_intimacy ",
                    "visual_prompt": " 近景。 ",
                    "model_visual_prompt": " intimate close shot ",
                    "negative_prompt": " round face "
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    paths = ProjectPaths(repo_root=tmp_path, project_name="premium-003-004")

    normalize_project_shots(paths)

    [normalized] = json.loads(shots_file.read_text(encoding="utf-8"))
    assert normalized["voice_type"] == "inner_voice"
    assert normalized["voice"] == "female_lead"
    assert normalized["action_goal"] == "重新稳住自己"
    assert normalized["motion_intent"] == "inner_voice_intimacy"
```

- [ ] **Step 2: Run the failing schema tests**

Run:

```bash
uv run --with pytest pytest tests/test_shots.py tests/test_build_shots.py -q
```

Expected: FAIL because `Shot` does not yet understand `voice_type`, `action_goal`, or `motion_intent`.

- [ ] **Step 3: Implement the richer shot schema**

In `scripts/local_video/shots.py`, extend the dataclass and parser like this:

```python
ALLOWED_VOICE_TYPES = {"silent", "narration", "inner_voice", "spoken"}
ALLOWED_MOTION_INTENTS = {
    "legacy_generic",
    "establishing_pressure",
    "silent_reaction",
    "inner_voice_intimacy",
    "silent_relationship_pressure",
    "spoken_hero",
}


@dataclass(frozen=True)
class Shot:
    id: str
    image: str
    duration_sec: float
    camera_motion: str
    voice: str
    dialogue: str
    subtitle: str
    voice_type: str = "spoken"
    action_goal: str = ""
    motion_intent: str = "legacy_generic"
    visual_prompt: str = ""
    model_visual_prompt: str = ""
    negative_prompt: str = ""

    @classmethod
    def from_dict(cls, payload: dict) -> "Shot":
        ...
        voice_type = str(payload.get("voice_type", "spoken")).strip()
        if voice_type not in ALLOWED_VOICE_TYPES:
            raise ValueError(f"Invalid voice_type: {voice_type}")

        motion_intent = str(payload.get("motion_intent", "legacy_generic")).strip()
        if motion_intent not in ALLOWED_MOTION_INTENTS:
            raise ValueError(f"Invalid motion_intent: {motion_intent}")

        voice = str(payload.get("voice", "")).strip()
        dialogue = str(payload.get("dialogue", "")).strip()
        subtitle = str(payload.get("subtitle", "")).strip()

        if voice_type != "silent" and not voice:
            raise ValueError("Non-silent shots must include a voice key")
        if voice_type == "silent":
            voice = ""
            dialogue = ""
            subtitle = ""

        return cls(
            ...,
            voice=voice,
            dialogue=dialogue,
            subtitle=subtitle,
            voice_type=voice_type,
            action_goal=str(payload.get("action_goal", "")).strip(),
            motion_intent=motion_intent,
            visual_prompt=str(payload.get("visual_prompt", "")),
            model_visual_prompt=str(payload.get("model_visual_prompt", "")),
            negative_prompt=str(payload.get("negative_prompt", "")),
        )
```

In `scripts/build_shots.py`, preserve the new fields:

```python
        normalized.append(
            Shot(
                id=shot.id,
                image=image_path.relative_to(paths.project_dir).as_posix(),
                duration_sec=shot.duration_sec,
                camera_motion=shot.camera_motion,
                voice=shot.voice.strip(),
                dialogue=shot.dialogue.strip(),
                subtitle=shot.subtitle.strip(),
                voice_type=shot.voice_type.strip(),
                action_goal=shot.action_goal.strip(),
                motion_intent=shot.motion_intent.strip(),
                visual_prompt=shot.visual_prompt.strip(),
                model_visual_prompt=shot.model_visual_prompt.strip(),
                negative_prompt=shot.negative_prompt.strip(),
            )
        )
```

- [ ] **Step 4: Run the schema tests again**

Run:

```bash
uv run --with pytest pytest tests/test_shots.py tests/test_build_shots.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit the shot-schema update**

```bash
git add scripts/local_video/shots.py scripts/build_shots.py tests/test_shots.py tests/test_build_shots.py
git commit -m "feat: add richer shot metadata for hybrid sample"
```

### Task 3: Surface Shot Intent In Prompt Generation And API Still Requests

**Files:**
- Modify: `scripts/local_video/prompts.py`
- Modify: `scripts/build_prompts.py`
- Modify: `scripts/generate_api_stills.py`
- Modify: `tests/test_prompts.py`
- Modify: `tests/test_build_prompts.py`
- Modify: `tests/test_generate_api_stills.py`

- [ ] **Step 1: Write failing prompt tests**

Add to `tests/test_prompts.py`:

```python
def test_render_shot_prompt_includes_voice_type_action_goal_and_motion_intent() -> None:
    shot = Shot(
        id="shot-001",
        image="stills/shot-001.png",
        duration_sec=5.0,
        camera_motion="slow_push_in",
        voice="female_lead",
        dialogue="他停得太近。",
        subtitle="他停得太近。",
        voice_type="inner_voice",
        action_goal="重新稳住自己",
        motion_intent="inner_voice_intimacy",
        visual_prompt="苏晚偏近景。",
    )

    prompt = render_shot_prompt(
        shot=shot,
        style_guide="premium palace manhua",
        character_anchors=[],
    )

    assert "Voice type: inner_voice" in prompt
    assert "Action goal: 重新稳住自己" in prompt
    assert "Motion intent: inner_voice_intimacy" in prompt
```

Add to `tests/test_generate_api_stills.py`:

```python
def test_generate_candidates_from_api_compact_prompt_mentions_action_goal(tmp_path: Path) -> None:
    paths = ProjectPaths(repo_root=tmp_path, project_name="premium-003-004")
    paths.project_dir.mkdir(parents=True, exist_ok=True)
    dump_shots(
        paths.shots_file,
        [
            Shot(
                id="shot-a",
                image="stills/shot-a.png",
                duration_sec=4.5,
                camera_motion="slow_push_in",
                voice="female_lead",
                dialogue="那一瞬，她先察觉到的，不是脚步。",
                subtitle="那一瞬，她先察觉到的，不是脚步。",
                voice_type="narration",
                action_goal="先静住，再抬眼",
                motion_intent="establishing_pressure",
                visual_prompt="宫廊夜色。",
                model_visual_prompt="moonlit corridor heroine",
                negative_prompt="round face",
            )
        ],
    )
    fake = FakeClient()

    generate_candidates_from_api(
        paths=paths,
        shot_ids=["shot-a"],
        client=fake,
        model="gpt-image-2",
        size="1024x1536",
        quality="high",
        output_format="png",
        variants=1,
        use_prompt_files=False,
    )

    prompt = fake.images.calls[0]["prompt"]
    assert "Voice mode: narration" in prompt
    assert "Action goal: 先静住，再抬眼" in prompt
    assert "Motion intent: establishing_pressure" in prompt
```

- [ ] **Step 2: Run the prompt tests and confirm they fail**

Run:

```bash
uv run --with pytest pytest tests/test_prompts.py tests/test_build_prompts.py tests/test_generate_api_stills.py -q
```

Expected: FAIL because the prompt builders still ignore the new shot metadata.

- [ ] **Step 3: Update prompt rendering and compact prompt generation**

In `scripts/local_video/prompts.py`, add a shot-performance section:

```python
    return (
        f"# {shot.id}\n\n"
        "## Image Target\n\n"
        "Create a vertical 9:16 cinematic manhua still for an AI short drama.\n\n"
        "## Global Style\n\n"
        f"{style_guide.strip()}\n\n"
        "## Character Anchors\n\n"
        f"{characters}\n\n"
        "## Shot Performance\n\n"
        f"Voice type: {shot.voice_type}\n"
        f"Action goal: {shot.action_goal or '-'}\n"
        f"Motion intent: {shot.motion_intent}\n\n"
        "## Shot Composition\n\n"
        f"{visual_prompt.strip()}\n\n"
        ...
    )
```

In `scripts/generate_api_stills.py`, enrich `_compact_shot_prompt_text()`:

```python
    bits = [
        style_guide,
        "Create one premium vertical 9:16 still with no text overlays.",
        f"Voice mode: {shot.voice_type}",
        f"Action goal: {shot.action_goal.strip()}",
        f"Motion intent: {shot.motion_intent.strip()}",
        shot.visual_prompt.strip(),
        shot.model_visual_prompt.strip(),
        " ".join(bit for bit in anchor_bits if bit),
        f"Dialogue context: {shot.subtitle.strip()}",
        f"Negative prompt: {shot.negative_prompt.strip()}",
    ]
```

No behavioral change is required in `scripts/build_prompts.py` beyond reusing the updated prompt writer.

- [ ] **Step 4: Run the prompt tests again**

Run:

```bash
uv run --with pytest pytest tests/test_prompts.py tests/test_build_prompts.py tests/test_generate_api_stills.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit the prompt update**

```bash
git add scripts/local_video/prompts.py scripts/generate_api_stills.py tests/test_prompts.py tests/test_build_prompts.py tests/test_generate_api_stills.py
git commit -m "feat: include shot intent in prompt generation"
```

### Task 4: Add A Switchable Audio Provider With Silent-Shot Support

**Files:**
- Modify: `scripts/local_video/project_paths.py`
- Modify: `scripts/local_video/audio_builder.py`
- Modify: `scripts/build_audio.py`
- Modify: `.env.example`
- Modify: `tests/test_build_audio.py`

- [ ] **Step 1: Write failing audio-provider tests**

Replace the top of `tests/test_build_audio.py` with imports that cover both providers:

```python
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.local_video.audio_builder import (
    AudioConfig,
    build_edge_tts_command,
    build_say_command,
    build_silent_audio_command,
    resolve_voice,
)
```

Add these tests:

```python
def test_resolve_voice_maps_hybrid_voice_keys() -> None:
    config = AudioConfig(
        provider="edge",
        female_voice="zh-CN-XiaoxiaoNeural",
        male_voice="zh-CN-YunxiNeural",
    )

    assert resolve_voice("female_lead", config) == "zh-CN-XiaoxiaoNeural"
    assert resolve_voice("male_regent", config) == "zh-CN-YunxiNeural"


def test_build_edge_tts_command_uses_expected_shape(tmp_path: Path) -> None:
    command = build_edge_tts_command(
        voice_name="zh-CN-XiaoxiaoNeural",
        text="你好",
        output_path=tmp_path / "shot-001.mp3",
    )

    assert command == [
        "edge-tts",
        "--voice",
        "zh-CN-XiaoxiaoNeural",
        "--text",
        "你好",
        "--write-media",
        str(tmp_path / "shot-001.mp3"),
    ]


def test_build_silent_audio_command_uses_anullsrc(tmp_path: Path) -> None:
    command = build_silent_audio_command(
        duration_sec=5.0,
        output_path=tmp_path / "shot-001.wav",
    )

    assert command[:6] == [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=channel_layout=stereo:sample_rate=44100",
    ]
    assert str(tmp_path / "shot-001.wav") == command[-1]
```

- [ ] **Step 2: Run the audio tests and verify they fail**

Run:

```bash
uv run --with pytest pytest tests/test_build_audio.py -q
```

Expected: FAIL because `AudioConfig`, `build_edge_tts_command`, and `build_silent_audio_command` do not exist yet.

- [ ] **Step 3: Implement the audio abstraction**

In `scripts/local_video/project_paths.py`, add reusable audio helpers:

```python
    def audio_output_path(self, shot_id: str, extension: str) -> Path:
        return self.audio_dir / f"{shot_id}{extension}"

    def resolve_audio_file(self, shot_id: str) -> Path:
        for extension in (".mp3", ".wav", ".aiff"):
            candidate = self.audio_output_path(shot_id, extension)
            if candidate.exists():
                return candidate
        raise FileNotFoundError(f"Missing audio file for shot: {shot_id}")
```

In `scripts/local_video/audio_builder.py`, add provider-aware configuration and silent-shot generation:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class AudioConfig:
    provider: str = "say"
    female_voice: str = "zh-CN-XiaoxiaoNeural"
    male_voice: str = "zh-CN-YunxiNeural"


def resolve_voice(voice_key: str, config: AudioConfig) -> str:
    voice_map = {
        "female_lead": config.female_voice,
        "male_regent": config.male_voice,
        "female_narrator": config.female_voice,
        "male_regent_legacy": config.male_voice,
    }
    try:
        return voice_map[voice_key]
    except KeyError as exc:
        raise ValueError(f"Unknown voice key: {voice_key}") from exc


def build_edge_tts_command(voice_name: str, text: str, output_path: Path) -> list[str]:
    return [
        "edge-tts",
        "--voice",
        voice_name,
        "--text",
        text,
        "--write-media",
        str(output_path),
    ]


def build_silent_audio_command(duration_sec: float, output_path: Path) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-t",
        str(duration_sec),
        str(output_path),
    ]
```

Then adapt `build_project_audio()`:

```python
def build_project_audio(paths: ProjectPaths, config: AudioConfig | None = None) -> dict[str, float]:
    config = config or AudioConfig()
    paths.ensure_generated_dirs()
    shots = load_shots(paths.shots_file)
    durations: dict[str, float] = {}

    for shot in shots:
        if shot.voice_type == "silent":
            output_path = paths.audio_output_path(shot.id, ".wav")
            subprocess.run(
                build_silent_audio_command(shot.duration_sec, output_path),
                check=True,
            )
            durations[shot.id] = 0.0
            continue

        voice_name = resolve_voice(shot.voice, config)
        if config.provider == "edge":
            output_path = paths.audio_output_path(shot.id, ".mp3")
            command = build_edge_tts_command(voice_name, shot.dialogue, output_path)
        else:
            output_path = paths.audio_output_path(shot.id, ".aiff")
            command = build_say_command(voice_name, shot.dialogue, output_path)

        subprocess.run(command, check=True)
        durations[shot.id] = measure_audio_duration(output_path)
```

In `scripts/build_audio.py`, thread provider options through the CLI:

```python
    parser.add_argument("--provider", default="say", choices=["say", "edge"])
    parser.add_argument("--female-voice", default="zh-CN-XiaoxiaoNeural")
    parser.add_argument("--male-voice", default="zh-CN-YunxiNeural")
```

And call:

```python
    durations = build_project_audio(
        paths,
        config=AudioConfig(
            provider=args.provider,
            female_voice=args.female_voice,
            male_voice=args.male_voice,
        ),
    )
```

Update `.env.example` to document the intended defaults:

```dotenv
NODE_ENV=development
OPENAI_API_KEY=
OPENAI_BASE_URL=
AUDIO_PROVIDER=edge
AUDIO_FEMALE_VOICE=zh-CN-XiaoxiaoNeural
AUDIO_MALE_VOICE=zh-CN-YunxiNeural
```

- [ ] **Step 4: Run the audio tests again**

Run:

```bash
uv run --with pytest pytest tests/test_build_audio.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit the audio-provider layer**

```bash
git add scripts/local_video/project_paths.py scripts/local_video/audio_builder.py scripts/build_audio.py .env.example tests/test_build_audio.py
git commit -m "feat: add switchable external audio provider"
```

### Task 5: Make Render Output Work With Silent Shots, Mixed Audio Formats, And Review Artifacts

**Files:**
- Modify: `scripts/local_video/project_paths.py`
- Modify: `scripts/local_video/rendering.py`
- Modify: `scripts/render_video.py`
- Modify: `tests/test_render_video.py`

- [ ] **Step 1: Write failing render tests**

Add to `tests/test_render_video.py`:

```python
def test_build_subtitles_skips_silent_shots_without_text() -> None:
    shots = [
        Shot(
            id="shot-001",
            image="stills/shot-001.png",
            duration_sec=4.0,
            camera_motion="static",
            voice="female_lead",
            dialogue="旁白",
            subtitle="旁白",
            voice_type="narration",
        ),
        Shot(
            id="shot-002",
            image="stills/shot-002.png",
            duration_sec=5.0,
            camera_motion="static",
            voice="",
            dialogue="",
            subtitle="",
            voice_type="silent",
        ),
    ]
    final_durations = {"shot-001": 4.0, "shot-002": 5.0}

    subtitles = build_subtitles(shots, final_durations)

    assert "旁白" in subtitles
    assert "shot-002" not in subtitles


def test_render_project_video_writes_review_manifest(monkeypatch, tmp_path: Path) -> None:
    paths = ProjectPaths(repo_root=tmp_path, project_name="demo-001")
    paths.project_dir.mkdir(parents=True)
    paths.stills_dir.mkdir(parents=True)
    paths.audio_dir.mkdir(parents=True)
    paths.build_dir.mkdir(parents=True)
    paths.video_clips_dir.mkdir(parents=True)
    (paths.stills_dir / "shot-001.png").write_bytes(b"still")
    (paths.audio_dir / "shot-001.mp3").write_bytes(b"audio")
    paths.video_clip_path("shot-001").write_bytes(b"video")
    paths.durations_file.write_text('{"shot-001": 4.2}\n', encoding="utf-8")
    dump_shots(
        paths.shots_file,
        [
            Shot(
                id="shot-001",
                image="stills/shot-001.png",
                duration_sec=4.5,
                camera_motion="slow_push_in",
                voice="female_lead",
                dialogue="旁白",
                subtitle="旁白",
                voice_type="narration",
                action_goal="先静住，再抬眼",
                motion_intent="establishing_pressure",
            )
        ],
    )

    def fake_run(command, check, capture_output=False, text=False):
        if command[:2] == ["ffmpeg", "-filters"]:
            return SimpleNamespace(stdout="")
        output_path = Path(command[-1])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(output_path.name.encode("utf-8"))
        return SimpleNamespace(stdout="", returncode=0)

    monkeypatch.setattr("scripts.render_video.subprocess.run", fake_run)

    render_project_video(paths)

    review_manifest = json.loads(
        paths.review_manifest_file.read_text(encoding="utf-8")
    )
    assert review_manifest["shots"][0]["shot_id"] == "shot-001"
    assert review_manifest["shots"][0]["audio_path"] == "audio/shot-001.mp3"
```

- [ ] **Step 2: Run the render tests and confirm they fail**

Run:

```bash
uv run --with pytest pytest tests/test_render_video.py -q
```

Expected: FAIL because subtitles still render every shot block and no review manifest exists yet.

- [ ] **Step 3: Implement render compatibility and review output**

In `scripts/local_video/project_paths.py`, add:

```python
    @property
    def review_manifest_file(self) -> Path:
        return self.build_dir / "review_manifest.json"
```

In `scripts/local_video/rendering.py`, make subtitles skip blank text:

```python
def build_subtitles(shots: list[Shot], final_durations: dict[str, float]) -> str:
    cursor = 0.0
    blocks: list[str] = []
    subtitle_index = 1
    for shot in shots:
        start = cursor
        end = cursor + final_durations[shot.id]
        if shot.subtitle.strip():
            blocks.append(
                "\n".join(
                    [
                        str(subtitle_index),
                        f"{format_srt_timestamp(start)} --> {format_srt_timestamp(end)}",
                        shot.subtitle,
                    ]
                )
            )
            subtitle_index += 1
        cursor = end
    return "\n\n".join(blocks) + ("\n" if blocks else "")
```

In `scripts/render_video.py`, resolve audio files generically and write a review manifest:

```python
    review_rows: list[dict[str, object]] = []
    for shot in shots:
        audio_path = paths.resolve_audio_file(shot.id)
        ...
        review_rows.append(
            {
                "shot_id": shot.id,
                "voice_type": shot.voice_type,
                "voice": shot.voice,
                "action_goal": shot.action_goal,
                "motion_intent": shot.motion_intent,
                "audio_path": audio_path.relative_to(paths.project_dir).as_posix(),
                "clip_path": clip_path.relative_to(paths.project_dir).as_posix(),
                "final_duration_sec": final_duration,
            }
        )

    paths.review_manifest_file.write_text(
        json.dumps({"shots": review_rows}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
```

- [ ] **Step 4: Run the render tests again**

Run:

```bash
uv run --with pytest pytest tests/test_render_video.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit the render updates**

```bash
git add scripts/local_video/project_paths.py scripts/local_video/rendering.py scripts/render_video.py tests/test_render_video.py
git commit -m "feat: add review-friendly hybrid render outputs"
```

### Task 6: Make Wan I2V Prompts Depend On Shot Purpose Instead Of One Generic Motion Recipe

**Files:**
- Modify: `scripts/wan22_i2v_generate.py`
- Modify: `tests/test_wan22_i2v_generate.py`

- [ ] **Step 1: Write failing motion-template tests**

Add to `tests/test_wan22_i2v_generate.py`:

```python
def test_generate_shot_video_uses_motion_intent_specific_prompt_text(tmp_path: Path) -> None:
    paths = ProjectPaths(repo_root=tmp_path, project_name="demo-001")
    paths.project_dir.mkdir(parents=True)
    paths.stills_dir.mkdir(parents=True)
    (paths.stills_dir / "shot-001.png").write_bytes(b"still")
    dump_shots(
        paths.shots_file,
        [
            Shot(
                id="shot-001",
                image="stills/shot-001.png",
                duration_sec=5.0,
                camera_motion="slow_push_in",
                voice="male_regent",
                dialogue="你，不是她。",
                subtitle="你，不是她。",
                voice_type="spoken",
                action_goal="压下来把一句话说狠",
                motion_intent="spoken_hero",
                model_visual_prompt="oppressive hero close-up of the regent prince",
                negative_prompt="round face",
            )
        ],
    )
    comfy_output = tmp_path / "comfy-output.mp4"
    comfy_output.write_bytes(b"video")
    client = FakeVideoClient(comfy_output)

    generate_shot_video(paths=paths, shot_id="shot-001", client=client, fps=12.0)

    prompt_text = client.submitted_prompts[0]["10"]["inputs"]["text"]
    negative_text = client.submitted_prompts[0]["11"]["inputs"]["text"]
    assert "restrained mouth movement" in prompt_text
    assert "stable lip region" in negative_text
```

- [ ] **Step 2: Run the Wan tests and verify they fail**

Run:

```bash
uv run --with pytest pytest tests/test_wan22_i2v_generate.py -q
```

Expected: FAIL because the Wan prompt text is still the same generic suffix for every shot.

- [ ] **Step 3: Add motion-intent prompt templates**

In `scripts/wan22_i2v_generate.py`, add helpers:

```python
def _motion_prompt_suffix(shot: Shot) -> tuple[str, str]:
    mapping = {
        "establishing_pressure": (
            "subtle posture settling, gentle eye-line shift, atmospheric corridor movement, stable identity",
            "flicker, jitter, morphing face, noisy background, stiff freeze",
        ),
        "silent_reaction": (
            "micro breath, slight shoulder tension, small gaze change, restrained reaction performance",
            "wide gesture, melodrama, face warping, frozen eyes",
        ),
        "inner_voice_intimacy": (
            "small head adjustment, intimate gaze hold, breath-led stillness, mouth mostly still",
            "visible speech flapping, lip wobble, jaw distortion, face morphing",
        ),
        "silent_relationship_pressure": (
            "compressed distance, sleeve drift, hand detail tension, controlled relationship pressure",
            "extra limbs, tangled bodies, chaotic overlap, jitter",
        ),
        "spoken_hero": (
            "restrained mouth movement, jaw tension, dangerous gaze hold, coherent anatomy, stable identity",
            "broken lip sync, unstable lip region, face morphing, flicker, jitter",
        ),
    }
    return mapping.get(
        shot.motion_intent,
        ("subtle breathing, slight eye blink, gentle head motion, soft fabric motion", "flicker, jitter, morphing face"),
    )
```

Then use it inside `generate_shot_video()`:

```python
    motion_suffix, motion_negative = _motion_prompt_suffix(shot)
    prompt_text = f"{shot.model_visual_prompt}, {motion_suffix}"
    negative_text = f"{shot.negative_prompt}, {motion_negative}, duplicate person, chaotic background, static freeze"
```

- [ ] **Step 4: Run the Wan tests again**

Run:

```bash
uv run --with pytest pytest tests/test_wan22_i2v_generate.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit the motion-template update**

```bash
git add scripts/wan22_i2v_generate.py tests/test_wan22_i2v_generate.py
git commit -m "feat: vary wan motion prompts by shot intent"
```

### Task 7: Thread The New Audio Path Through The Entry Script And Define The Operator Pass

**Files:**
- Modify: `scripts/run_demo.py`
- Modify: `tests/test_run_demo.py`

- [ ] **Step 1: Write the failing entrypoint test**

Replace `tests/test_run_demo.py` with:

```python
from pathlib import Path

from scripts.local_video.project_paths import ProjectPaths
from scripts.run_demo import run_pipeline


def test_run_pipeline_calls_three_steps_in_order_with_audio_provider(monkeypatch) -> None:
    events: list[tuple[str, object]] = []

    monkeypatch.setattr(
        "scripts.run_demo.normalize_project_shots",
        lambda paths: events.append(("shots", paths.project_name)) or 5,
    )
    monkeypatch.setattr(
        "scripts.run_demo.build_project_audio",
        lambda paths, config=None: events.append(("audio", config.provider)) or {"shot-a": 4.2},
    )
    monkeypatch.setattr(
        "scripts.run_demo.render_project_video",
        lambda paths: events.append(("render", paths.project_name)) or paths.render_output,
    )

    run_pipeline(
        ProjectPaths(repo_root=Path("/tmp/repo"), project_name="premium-003-004"),
        audio_provider="edge",
        female_voice="zh-CN-XiaoxiaoNeural",
        male_voice="zh-CN-YunxiNeural",
    )

    assert events == [
        ("shots", "premium-003-004"),
        ("audio", "edge"),
        ("render", "premium-003-004"),
    ]
```

- [ ] **Step 2: Run the entrypoint test and verify it fails**

Run:

```bash
uv run --with pytest pytest tests/test_run_demo.py -q
```

Expected: FAIL because `run_pipeline()` does not yet accept audio-provider parameters.

- [ ] **Step 3: Update the entrypoint and record the operator commands**

In `scripts/run_demo.py`, thread the audio config through:

```python
from scripts.local_video.audio_builder import AudioConfig


def run_pipeline(
    paths: ProjectPaths,
    audio_provider: str = "say",
    female_voice: str = "zh-CN-XiaoxiaoNeural",
    male_voice: str = "zh-CN-YunxiNeural",
) -> Path:
    normalize_project_shots(paths)
    build_project_audio(
        paths,
        config=AudioConfig(
            provider=audio_provider,
            female_voice=female_voice,
            male_voice=male_voice,
        ),
    )
    return render_project_video(paths)
```

Extend the CLI:

```python
    parser.add_argument("--audio-provider", default="say", choices=["say", "edge"])
    parser.add_argument("--female-voice", default="zh-CN-XiaoxiaoNeural")
    parser.add_argument("--male-voice", default="zh-CN-YunxiNeural")
```

And call:

```python
    output_path = run_pipeline(
        paths,
        audio_provider=args.audio_provider,
        female_voice=args.female_voice,
        male_voice=args.male_voice,
    )
```

Operator pass for the longer hybrid sample:

```bash
export PATH="$HOME/homebrew/Cellar/ffmpeg/8.1.1/bin:$PATH"
export OPENAI_API_KEY='...'
export OPENAI_BASE_URL='https://gohok.top'

uv run --with pytest pytest \
  tests/test_premium_sample_project.py \
  tests/test_shots.py \
  tests/test_build_shots.py \
  tests/test_prompts.py \
  tests/test_build_prompts.py \
  tests/test_generate_api_stills.py \
  tests/test_build_audio.py \
  tests/test_wan22_i2v_generate.py \
  tests/test_render_video.py \
  tests/test_run_demo.py -q

uv run python scripts/build_prompts.py --project premium-003-004

uv run --with openai python scripts/generate_api_stills.py \
  --project premium-003-004 \
  --all-shots \
  --variants 1 \
  --model gpt-image-2 \
  --size 1024x1536 \
  --quality high \
  --compact-prompt

# manually promote one selected still per shot with existing still-selection flow

uv run --with edge-tts python scripts/build_audio.py \
  --project premium-003-004 \
  --provider edge \
  --female-voice zh-CN-XiaoxiaoNeural \
  --male-voice zh-CN-YunxiNeural

uv run python scripts/wan22_i2v_generate.py \
  --project premium-003-004 \
  --all-shots \
  --base-url http://127.0.0.1:8188 \
  --output-dir '/Users/kelton/ai漫剧/ComfyUI/output' \
  --width 384 \
  --height 672 \
  --fps 12 \
  --preview-duration-sec 5.0 \
  --seed 424242

uv run python scripts/render_video.py --project premium-003-004
```

- [ ] **Step 4: Run the entrypoint test and the narrow regression set**

Run:

```bash
uv run --with pytest pytest tests/test_run_demo.py tests/test_build_audio.py tests/test_render_video.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit the entrypoint wiring**

```bash
git add scripts/run_demo.py tests/test_run_demo.py
git commit -m "feat: thread hybrid audio config through pipeline entrypoint"
```

---

## Self-Review Checklist

**Spec coverage**
- Longer `24-30 second` sample: Task 1
- Five-shot structure: Task 1
- Explicit `voice_type`, `action_goal`, `motion_intent`: Task 2
- Narration / inner voice / spoken split in prompts: Task 3
- Better external voice source and unified voices: Task 4
- Silent-shot handling and review outputs: Task 5
- Motion templates by shot purpose: Task 6
- Updated end-to-end operator flow: Task 7

**Placeholder scan**
- No `TBD`, `TODO`, or “handle later” markers are allowed in implementation edits.
- If a step below this plan needs a new helper, define it in the same task before using it.

**Type consistency**
- `voice_type` values must stay exactly: `silent`, `narration`, `inner_voice`, `spoken`
- `motion_intent` values must stay exactly:
  - `legacy_generic`
  - `establishing_pressure`
  - `silent_reaction`
  - `inner_voice_intimacy`
  - `silent_relationship_pressure`
  - `spoken_hero`
- Hybrid audio keys must stay exactly: `female_lead`, `male_regent`

