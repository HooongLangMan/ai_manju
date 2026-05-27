# Local Ancient Transmigration MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local, repeatable workflow that renders one short "ancient costume transmigration system" demo video from hand-authored shot data, static still images, local TTS, subtitles, and `ffmpeg`.

**Architecture:** Keep the repo shape narrow: use `storage/projects/demo-001/` for authored and generated assets, `storage/renders/` for the final `mp4`, and a small Python package under `scripts/local_video/` for reusable logic. Thin CLI scripts under `scripts/` orchestrate validation, TTS generation, and rendering in sequence so later providers can replace local tools without changing project data.

**Tech Stack:** Python 3.9 standard library, `uv`, `pytest`, macOS `say`, `ffmpeg`/`ffprobe`, ImageMagick

---

## File Structure

The implementation should introduce these focused files:

- Create: `.gitignore`
  Purpose: keep generated audio, build artifacts, render outputs, and `.codegraph/` out of git.
- Create: `scripts/__init__.py`
  Purpose: allow test imports from `scripts.*`.
- Create: `scripts/local_video/__init__.py`
  Purpose: mark the local video helpers as a package.
- Create: `scripts/local_video/project_paths.py`
  Purpose: centralize project-relative paths and output directory creation.
- Create: `scripts/local_video/shots.py`
  Purpose: define the `Shot` model, allowed camera motions, and JSON load/dump helpers.
- Create: `scripts/local_video/audio_builder.py`
  Purpose: voice mapping, `say` command generation, `ffprobe` duration measurement, and duration manifest writing.
- Create: `scripts/local_video/rendering.py`
  Purpose: subtitle generation, duration math, `ffmpeg` filter/command construction, and concat manifest generation.
- Create: `scripts/build_shots.py`
  Purpose: validate and normalize a project's authored `shots.json`.
- Create: `scripts/build_audio.py`
  Purpose: generate shot audio and `durations.json`.
- Create: `scripts/render_video.py`
  Purpose: render shot clips, concatenate them, burn subtitles, and write the final `mp4`.
- Create: `scripts/run_demo.py`
  Purpose: run the three main steps in order for `demo-001`.
- Create: `storage/projects/demo-001/story.md`
  Purpose: store the authored story reference for the first demo.
- Create: `storage/projects/demo-001/shots.json`
  Purpose: store the authored four-shot input data.
- Create: `storage/projects/demo-001/stills/shot-001.png`
- Create: `storage/projects/demo-001/stills/shot-002.png`
- Create: `storage/projects/demo-001/stills/shot-003.png`
- Create: `storage/projects/demo-001/stills/shot-004.png`
  Purpose: placeholder stills for the first fully local render.
- Create: `tests/test_shots.py`
  Purpose: validate path layout and shot schema behavior.
- Create: `tests/test_build_shots.py`
  Purpose: validate project shot normalization behavior.
- Create: `tests/test_build_audio.py`
  Purpose: validate voice mapping and audio duration helpers.
- Create: `tests/test_render_video.py`
  Purpose: validate subtitle timing, duration math, and motion filter building.
- Create: `tests/test_run_demo.py`
  Purpose: validate orchestration order for the end-to-end runner.

### Task 1: Scaffold Shared Helpers

**Files:**
- Create: `/Users/kelton/ai漫剧/ai-manga-studio/.gitignore`
- Create: `/Users/kelton/ai漫剧/ai-manga-studio/scripts/__init__.py`
- Create: `/Users/kelton/ai漫剧/ai-manga-studio/scripts/local_video/__init__.py`
- Create: `/Users/kelton/ai漫剧/ai-manga-studio/scripts/local_video/project_paths.py`
- Create: `/Users/kelton/ai漫剧/ai-manga-studio/scripts/local_video/shots.py`
- Test: `/Users/kelton/ai漫剧/ai-manga-studio/tests/test_shots.py`

- [ ] **Step 1: Write the failing shared-helper tests**

```python
# /Users/kelton/ai漫剧/ai-manga-studio/tests/test_shots.py
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
```

- [ ] **Step 2: Run the shared-helper tests to verify they fail**

Run: `uv run --with pytest pytest /Users/kelton/ai漫剧/ai-manga-studio/tests/test_shots.py -v`

Expected: FAIL with `ModuleNotFoundError` for `scripts.local_video.project_paths` or `scripts.local_video.shots`

- [ ] **Step 3: Write the minimal shared-helper implementation**

```python
# /Users/kelton/ai漫剧/ai-manga-studio/.gitignore
.codegraph/
__pycache__/
.pytest_cache/
*.pyc
storage/projects/*/audio/
storage/projects/*/build/
storage/renders/*.mp4
```

```python
# /Users/kelton/ai漫剧/ai-manga-studio/scripts/__init__.py
"""Top-level package for local workflow scripts."""
```

```python
# /Users/kelton/ai漫剧/ai-manga-studio/scripts/local_video/__init__.py
"""Reusable helpers for the local ancient transmigration MVP."""
```

```python
# /Users/kelton/ai漫剧/ai-manga-studio/scripts/local_video/project_paths.py
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    repo_root: Path
    project_name: str
    render_filename: str = "episode-001.mp4"

    @property
    def project_dir(self) -> Path:
        return self.repo_root / "storage" / "projects" / self.project_name

    @property
    def story_file(self) -> Path:
        return self.project_dir / "story.md"

    @property
    def shots_file(self) -> Path:
        return self.project_dir / "shots.json"

    @property
    def stills_dir(self) -> Path:
        return self.project_dir / "stills"

    @property
    def audio_dir(self) -> Path:
        return self.project_dir / "audio"

    @property
    def build_dir(self) -> Path:
        return self.project_dir / "build"

    @property
    def durations_file(self) -> Path:
        return self.build_dir / "durations.json"

    @property
    def subtitle_file(self) -> Path:
        return self.build_dir / "subtitles.srt"

    @property
    def render_dir(self) -> Path:
        return self.repo_root / "storage" / "renders"

    @property
    def render_output(self) -> Path:
        return self.render_dir / self.render_filename

    def ensure_generated_dirs(self) -> None:
        for path in (self.audio_dir, self.build_dir, self.render_dir):
            path.mkdir(parents=True, exist_ok=True)
```

```python
# /Users/kelton/ai漫剧/ai-manga-studio/scripts/local_video/shots.py
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Iterable


ALLOWED_CAMERA_MOTIONS = {
    "static",
    "slow_push_in",
    "slow_pan_left",
    "slow_pan_right",
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

    @classmethod
    def from_dict(cls, payload: dict) -> "Shot":
        required = {
            "id",
            "image",
            "duration_sec",
            "camera_motion",
            "voice",
            "dialogue",
            "subtitle",
        }
        missing = sorted(required - payload.keys())
        if missing:
            raise ValueError(f"Missing required shot fields: {', '.join(missing)}")

        camera_motion = str(payload["camera_motion"])
        if camera_motion not in ALLOWED_CAMERA_MOTIONS:
            raise ValueError(f"Invalid camera_motion: {camera_motion}")

        duration_sec = float(payload["duration_sec"])
        if duration_sec <= 0:
            raise ValueError("duration_sec must be greater than 0")

        return cls(
            id=str(payload["id"]),
            image=str(payload["image"]),
            duration_sec=duration_sec,
            camera_motion=camera_motion,
            voice=str(payload["voice"]),
            dialogue=str(payload["dialogue"]),
            subtitle=str(payload["subtitle"]),
        )


def load_shots(path: Path) -> list[Shot]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not payload:
        raise ValueError("shots.json must contain a non-empty list of shots")
    return [Shot.from_dict(item) for item in payload]


def dump_shots(path: Path, shots: Iterable[Shot]) -> None:
    serialized = [asdict(shot) for shot in shots]
    path.write_text(
        json.dumps(serialized, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
```

- [ ] **Step 4: Run the shared-helper tests to verify they pass**

Run: `uv run --with pytest pytest /Users/kelton/ai漫剧/ai-manga-studio/tests/test_shots.py -v`

Expected: PASS with `3 passed`

- [ ] **Step 5: Commit the shared-helper scaffold**

```bash
git -C /Users/kelton/ai漫剧/ai-manga-studio add \
  .gitignore \
  scripts/__init__.py \
  scripts/local_video/__init__.py \
  scripts/local_video/project_paths.py \
  scripts/local_video/shots.py \
  tests/test_shots.py
git -C /Users/kelton/ai漫剧/ai-manga-studio commit -m "feat: add local video shot schema helpers"
```

### Task 2: Author Demo Inputs And Validate `shots.json`

**Files:**
- Create: `/Users/kelton/ai漫剧/ai-manga-studio/storage/projects/demo-001/story.md`
- Create: `/Users/kelton/ai漫剧/ai-manga-studio/storage/projects/demo-001/shots.json`
- Create: `/Users/kelton/ai漫剧/ai-manga-studio/scripts/build_shots.py`
- Test: `/Users/kelton/ai漫剧/ai-manga-studio/tests/test_build_shots.py`

- [ ] **Step 1: Write the failing `build_shots` tests**

```python
# /Users/kelton/ai漫剧/ai-manga-studio/tests/test_build_shots.py
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
```

- [ ] **Step 2: Run the `build_shots` tests to verify they fail**

Run: `uv run --with pytest pytest /Users/kelton/ai漫剧/ai-manga-studio/tests/test_build_shots.py -v`

Expected: FAIL with `ModuleNotFoundError` for `scripts.build_shots`

- [ ] **Step 3: Write the demo story, demo shots, and `build_shots` validator**

```markdown
# /Users/kelton/ai漫剧/ai-manga-studio/storage/projects/demo-001/story.md
# 古风穿越系统 Demo

苏晚在冷宫中惊醒，发现自己从现代手术台穿越成了深宫弃妃。
就在她以为自己必死无疑时，一道金色系统面板在眼前展开。
系统要求她在三日之内接近权倾朝野的摄政王，否则直接抹杀。
她压下惊慌，在回廊尽头第一次撞见那个传闻中冷血无情的男人。
男人只看了她一眼，低声道：“你不是她。”
```

```json
// /Users/kelton/ai漫剧/ai-manga-studio/storage/projects/demo-001/shots.json
[
  {
    "id": "shot-001",
    "image": "stills/shot-001.png",
    "duration_sec": 6,
    "camera_motion": "slow_push_in",
    "voice": "female_narrator",
    "dialogue": "我不是应该死在手术台上吗？这里，怎么会是冷宫？",
    "subtitle": "我不是应该死在手术台上吗？这里，怎么会是冷宫？"
  },
  {
    "id": "shot-002",
    "image": "stills/shot-002.png",
    "duration_sec": 5,
    "camera_motion": "static",
    "voice": "system_voice",
    "dialogue": "系统提示：三日内接近摄政王，否则立即抹杀。",
    "subtitle": "系统提示：三日内接近摄政王，否则立即抹杀。"
  },
  {
    "id": "shot-003",
    "image": "stills/shot-003.png",
    "duration_sec": 6,
    "camera_motion": "slow_pan_left",
    "voice": "female_narrator",
    "dialogue": "苏晚攥紧衣袖，抬眼便撞进那人冷得像雪的目光里。",
    "subtitle": "苏晚攥紧衣袖，抬眼便撞进那人冷得像雪的目光里。"
  },
  {
    "id": "shot-004",
    "image": "stills/shot-004.png",
    "duration_sec": 5,
    "camera_motion": "slow_pan_right",
    "voice": "male_regent",
    "dialogue": "你，不是她。",
    "subtitle": "你，不是她。"
  }
]
```

```python
# /Users/kelton/ai漫剧/ai-manga-studio/scripts/build_shots.py
#!/usr/bin/env python3
from argparse import ArgumentParser
from pathlib import Path

from scripts.local_video.project_paths import ProjectPaths
from scripts.local_video.shots import Shot, dump_shots, load_shots


def normalize_project_shots(paths: ProjectPaths) -> int:
    if not paths.story_file.exists():
        raise FileNotFoundError(f"Missing story.md: {paths.story_file}")
    if not paths.shots_file.exists():
        raise FileNotFoundError(f"Missing shots.json: {paths.shots_file}")

    shots = load_shots(paths.shots_file)
    normalized: list[Shot] = []
    for shot in shots:
        image_path = paths.project_dir / shot.image
        if image_path.is_absolute():
            raise ValueError(f"Shot image must be project-relative: {shot.image}")
        if not image_path.exists():
            raise FileNotFoundError(f"Missing still image: {image_path}")

        normalized.append(
            Shot(
                id=shot.id,
                image=image_path.relative_to(paths.project_dir).as_posix(),
                duration_sec=shot.duration_sec,
                camera_motion=shot.camera_motion,
                voice=shot.voice,
                dialogue=shot.dialogue.strip(),
                subtitle=shot.subtitle.strip(),
            )
        )

    dump_shots(paths.shots_file, normalized)
    return len(normalized)


def parse_args() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("--project", default="demo-001")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
    )
    return parser


def main() -> None:
    args = parse_args().parse_args()
    paths = ProjectPaths(repo_root=Path(args.repo_root), project_name=args.project)
    count = normalize_project_shots(paths)
    print(f"Normalized {count} shots for {args.project}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the `build_shots` tests to verify they pass**

Run: `uv run --with pytest pytest /Users/kelton/ai漫剧/ai-manga-studio/tests/test_build_shots.py -v`

Expected: PASS with `2 passed`

- [ ] **Step 5: Commit the demo inputs and shot validator**

```bash
git -C /Users/kelton/ai漫剧/ai-manga-studio add \
  storage/projects/demo-001/story.md \
  storage/projects/demo-001/shots.json \
  scripts/build_shots.py \
  tests/test_build_shots.py
git -C /Users/kelton/ai漫剧/ai-manga-studio commit -m "feat: add demo story and shot validator"
```

### Task 3: Build Local TTS Audio And Durations

**Files:**
- Create: `/Users/kelton/ai漫剧/ai-manga-studio/scripts/local_video/audio_builder.py`
- Create: `/Users/kelton/ai漫剧/ai-manga-studio/scripts/build_audio.py`
- Test: `/Users/kelton/ai漫剧/ai-manga-studio/tests/test_build_audio.py`

- [ ] **Step 1: Write the failing audio-builder tests**

```python
# /Users/kelton/ai漫剧/ai-manga-studio/tests/test_build_audio.py
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.local_video.audio_builder import (
    build_say_command,
    measure_audio_duration,
    resolve_voice,
)


def test_resolve_voice_maps_demo_voice_keys() -> None:
    assert resolve_voice("female_narrator") == "Tingting"
    assert resolve_voice("system_voice") == "Meijia"
    assert resolve_voice("male_regent") == "Sinji"


def test_resolve_voice_rejects_unknown_key() -> None:
    with pytest.raises(ValueError, match="Unknown voice key"):
        resolve_voice("villain")


def test_build_say_command_uses_expected_shape(tmp_path: Path) -> None:
    command = build_say_command(
        voice_name="Tingting",
        text="你好",
        output_path=tmp_path / "shot-001.aiff",
    )

    assert command == [
        "say",
        "-v",
        "Tingting",
        "-o",
        str(tmp_path / "shot-001.aiff"),
        "你好",
    ]


def test_measure_audio_duration_parses_ffprobe_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_run(*args, **kwargs):
        return SimpleNamespace(stdout="4.250\n")

    monkeypatch.setattr(
        "scripts.local_video.audio_builder.subprocess.run",
        fake_run,
    )

    duration = measure_audio_duration(tmp_path / "shot-001.aiff")

    assert duration == 4.25
```

- [ ] **Step 2: Run the audio-builder tests to verify they fail**

Run: `uv run --with pytest pytest /Users/kelton/ai漫剧/ai-manga-studio/tests/test_build_audio.py -v`

Expected: FAIL with `ModuleNotFoundError` for `scripts.local_video.audio_builder`

- [ ] **Step 3: Write the minimal audio-builder implementation**

```python
# /Users/kelton/ai漫剧/ai-manga-studio/scripts/local_video/audio_builder.py
import json
from pathlib import Path
import subprocess

from scripts.local_video.project_paths import ProjectPaths
from scripts.local_video.shots import load_shots


VOICE_MAP = {
    "female_narrator": "Tingting",
    "system_voice": "Meijia",
    "male_regent": "Sinji",
}


def resolve_voice(voice_key: str) -> str:
    try:
        return VOICE_MAP[voice_key]
    except KeyError as exc:
        raise ValueError(f"Unknown voice key: {voice_key}") from exc


def build_say_command(voice_name: str, text: str, output_path: Path) -> list[str]:
    return ["say", "-v", voice_name, "-o", str(output_path), text]


def measure_audio_duration(audio_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return round(float(result.stdout.strip()), 3)


def build_project_audio(paths: ProjectPaths) -> dict[str, float]:
    paths.ensure_generated_dirs()
    shots = load_shots(paths.shots_file)
    durations: dict[str, float] = {}

    for shot in shots:
        output_path = paths.audio_dir / f"{shot.id}.aiff"
        subprocess.run(
            build_say_command(resolve_voice(shot.voice), shot.dialogue, output_path),
            check=True,
        )
        durations[shot.id] = measure_audio_duration(output_path)

    paths.durations_file.write_text(
        json.dumps(durations, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return durations
```

```python
# /Users/kelton/ai漫剧/ai-manga-studio/scripts/build_audio.py
#!/usr/bin/env python3
from argparse import ArgumentParser
from pathlib import Path

from scripts.local_video.audio_builder import build_project_audio
from scripts.local_video.project_paths import ProjectPaths


def parse_args() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("--project", default="demo-001")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
    )
    return parser


def main() -> None:
    args = parse_args().parse_args()
    paths = ProjectPaths(repo_root=Path(args.repo_root), project_name=args.project)
    durations = build_project_audio(paths)
    print(f"Generated audio for {len(durations)} shots")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the audio-builder tests to verify they pass**

Run: `uv run --with pytest pytest /Users/kelton/ai漫剧/ai-manga-studio/tests/test_build_audio.py -v`

Expected: PASS with `4 passed`

- [ ] **Step 5: Commit the audio builder**

```bash
git -C /Users/kelton/ai漫剧/ai-manga-studio add \
  scripts/local_video/audio_builder.py \
  scripts/build_audio.py \
  tests/test_build_audio.py
git -C /Users/kelton/ai漫剧/ai-manga-studio commit -m "feat: add local tts audio builder"
```

### Task 4: Render Shot Clips, Subtitles, And Final Video

**Files:**
- Create: `/Users/kelton/ai漫剧/ai-manga-studio/scripts/local_video/rendering.py`
- Create: `/Users/kelton/ai漫剧/ai-manga-studio/scripts/render_video.py`
- Test: `/Users/kelton/ai漫剧/ai-manga-studio/tests/test_render_video.py`

- [ ] **Step 1: Write the failing renderer tests**

```python
# /Users/kelton/ai漫剧/ai-manga-studio/tests/test_render_video.py
from scripts.local_video.rendering import (
    build_motion_filter,
    build_subtitles,
    compute_final_duration,
)
from scripts.local_video.shots import Shot


def test_compute_final_duration_respects_audio_tail_buffer() -> None:
    assert compute_final_duration(5.0, 3.0) == 5.0
    assert compute_final_duration(5.0, 5.2) == 5.8


def test_build_subtitles_uses_cumulative_shot_timing() -> None:
    shots = [
        Shot(
            id="shot-001",
            image="stills/shot-001.png",
            duration_sec=6.0,
            camera_motion="static",
            voice="female_narrator",
            dialogue="a",
            subtitle="第一句",
        ),
        Shot(
            id="shot-002",
            image="stills/shot-002.png",
            duration_sec=5.0,
            camera_motion="static",
            voice="system_voice",
            dialogue="b",
            subtitle="第二句",
        ),
    ]
    final_durations = {"shot-001": 6.0, "shot-002": 5.8}

    subtitles = build_subtitles(shots, final_durations)

    assert "00:00:00,000 --> 00:00:06,000" in subtitles
    assert "00:00:06,000 --> 00:00:11,800" in subtitles
    assert "第一句" in subtitles
    assert "第二句" in subtitles


def test_build_motion_filter_rejects_unknown_motion() -> None:
    try:
        build_motion_filter("orbit", 5.0)
    except ValueError as exc:
        assert "Unknown camera motion" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
```

- [ ] **Step 2: Run the renderer tests to verify they fail**

Run: `uv run --with pytest pytest /Users/kelton/ai漫剧/ai-manga-studio/tests/test_render_video.py -v`

Expected: FAIL with `ModuleNotFoundError` for `scripts.local_video.rendering`

- [ ] **Step 3: Write the renderer helpers and CLI**

```python
# /Users/kelton/ai漫剧/ai-manga-studio/scripts/local_video/rendering.py
from pathlib import Path

from scripts.local_video.shots import Shot


FPS = 24
FRAME_WIDTH = 1080
FRAME_HEIGHT = 1920
AUDIO_TAIL_BUFFER = 0.6


def compute_final_duration(min_duration: float, audio_duration: float) -> float:
    return round(max(min_duration, audio_duration + AUDIO_TAIL_BUFFER), 3)


def format_srt_timestamp(seconds: float) -> str:
    total_ms = int(round(seconds * 1000))
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def build_subtitles(shots: list[Shot], final_durations: dict[str, float]) -> str:
    cursor = 0.0
    blocks: list[str] = []
    for index, shot in enumerate(shots, start=1):
        start = cursor
        end = cursor + final_durations[shot.id]
        blocks.append(
            "\n".join(
                [
                    str(index),
                    f"{format_srt_timestamp(start)} --> {format_srt_timestamp(end)}",
                    shot.subtitle,
                ]
            )
        )
        cursor = end
    return "\n\n".join(blocks) + "\n"


def build_motion_filter(camera_motion: str, duration_sec: float) -> str:
    if camera_motion == "static":
        return (
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,fps=24,format=yuv420p"
        )
    if camera_motion == "slow_push_in":
        frames = max(int(duration_sec * FPS), 1)
        return (
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            f"zoompan=z='min(zoom+0.0007,1.08)':d={frames}:s=1080x1920:fps=24,"
            "format=yuv420p"
        )
    if camera_motion == "slow_pan_left":
        return (
            "scale=1188:2112,"
            f"crop=1080:1920:x='(in_w-out_w)*(1-min(t/{duration_sec},1))':"
            "y='(in_h-out_h)/2',fps=24,format=yuv420p"
        )
    if camera_motion == "slow_pan_right":
        return (
            "scale=1188:2112,"
            f"crop=1080:1920:x='(in_w-out_w)*min(t/{duration_sec},1)':"
            "y='(in_h-out_h)/2',fps=24,format=yuv420p"
        )
    raise ValueError(f"Unknown camera motion: {camera_motion}")


def build_clip_command(
    image_path: Path,
    audio_path: Path,
    output_path: Path,
    camera_motion: str,
    duration_sec: float,
) -> list[str]:
    return [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        str(image_path),
        "-i",
        str(audio_path),
        "-vf",
        build_motion_filter(camera_motion, duration_sec),
        "-t",
        str(duration_sec),
        "-r",
        str(FPS),
        "-pix_fmt",
        "yuv420p",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        str(output_path),
    ]


def build_concat_manifest(clip_paths: list[Path]) -> str:
    return "\n".join(f"file '{path}'" for path in clip_paths) + "\n"
```

```python
# /Users/kelton/ai漫剧/ai-manga-studio/scripts/render_video.py
#!/usr/bin/env python3
from argparse import ArgumentParser
import json
from pathlib import Path
import subprocess

from scripts.local_video.project_paths import ProjectPaths
from scripts.local_video.rendering import (
    build_clip_command,
    build_concat_manifest,
    build_subtitles,
    compute_final_duration,
)
from scripts.local_video.shots import load_shots


def load_durations(path: Path) -> dict[str, float]:
    if not path.exists():
        raise FileNotFoundError(f"Missing durations.json: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {shot_id: float(duration) for shot_id, duration in payload.items()}


def render_project_video(paths: ProjectPaths) -> Path:
    paths.ensure_generated_dirs()
    shots = load_shots(paths.shots_file)
    durations = load_durations(paths.durations_file)

    final_durations: dict[str, float] = {}
    clip_paths: list[Path] = []
    for shot in shots:
        audio_path = paths.audio_dir / f"{shot.id}.aiff"
        if not audio_path.exists():
            raise FileNotFoundError(f"Missing audio file: {audio_path}")

        final_duration = compute_final_duration(
            shot.duration_sec, durations[shot.id]
        )
        final_durations[shot.id] = final_duration

        clip_path = paths.build_dir / f"{shot.id}.mp4"
        subprocess.run(
            build_clip_command(
                image_path=paths.project_dir / shot.image,
                audio_path=audio_path,
                output_path=clip_path,
                camera_motion=shot.camera_motion,
                duration_sec=final_duration,
            ),
            check=True,
        )
        clip_paths.append(clip_path)

    paths.subtitle_file.write_text(
        build_subtitles(shots, final_durations),
        encoding="utf-8",
    )

    concat_manifest = paths.build_dir / "concat.txt"
    concat_manifest.write_text(build_concat_manifest(clip_paths), encoding="utf-8")

    plain_video = paths.build_dir / "episode-001-plain.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_manifest),
            "-c",
            "copy",
            str(plain_video),
        ],
        check=True,
    )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(plain_video),
            "-vf",
            f"subtitles={paths.subtitle_file}",
            "-c:v",
            "libx264",
            "-c:a",
            "copy",
            str(paths.render_output),
        ],
        check=True,
    )

    return paths.render_output


def parse_args() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("--project", default="demo-001")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
    )
    return parser


def main() -> None:
    args = parse_args().parse_args()
    paths = ProjectPaths(repo_root=Path(args.repo_root), project_name=args.project)
    output_path = render_project_video(paths)
    print(f"Rendered final video: {output_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the renderer tests to verify they pass**

Run: `uv run --with pytest pytest /Users/kelton/ai漫剧/ai-manga-studio/tests/test_render_video.py -v`

Expected: PASS with `3 passed`

- [ ] **Step 5: Commit the renderer**

```bash
git -C /Users/kelton/ai漫剧/ai-manga-studio add \
  scripts/local_video/rendering.py \
  scripts/render_video.py \
  tests/test_render_video.py
git -C /Users/kelton/ai漫剧/ai-manga-studio commit -m "feat: add local video renderer"
```

### Task 5: Add Demo Runner, Placeholder Stills, And Smoke Verification

**Files:**
- Create: `/Users/kelton/ai漫剧/ai-manga-studio/scripts/run_demo.py`
- Create: `/Users/kelton/ai漫剧/ai-manga-studio/storage/projects/demo-001/stills/shot-001.png`
- Create: `/Users/kelton/ai漫剧/ai-manga-studio/storage/projects/demo-001/stills/shot-002.png`
- Create: `/Users/kelton/ai漫剧/ai-manga-studio/storage/projects/demo-001/stills/shot-003.png`
- Create: `/Users/kelton/ai漫剧/ai-manga-studio/storage/projects/demo-001/stills/shot-004.png`
- Test: `/Users/kelton/ai漫剧/ai-manga-studio/tests/test_run_demo.py`

- [ ] **Step 1: Write the failing demo-runner test**

```python
# /Users/kelton/ai漫剧/ai-manga-studio/tests/test_run_demo.py
from pathlib import Path

from scripts.local_video.project_paths import ProjectPaths
from scripts.run_demo import run_pipeline


def test_run_pipeline_calls_three_steps_in_order(monkeypatch) -> None:
    events: list[str] = []

    monkeypatch.setattr(
        "scripts.run_demo.normalize_project_shots",
        lambda paths: events.append("shots") or 4,
    )
    monkeypatch.setattr(
        "scripts.run_demo.build_project_audio",
        lambda paths: events.append("audio") or {"shot-001": 4.2},
    )
    monkeypatch.setattr(
        "scripts.run_demo.render_project_video",
        lambda paths: events.append("render") or paths.render_output,
    )

    run_pipeline(ProjectPaths(repo_root=Path("/tmp/repo"), project_name="demo-001"))

    assert events == ["shots", "audio", "render"]
```

- [ ] **Step 2: Run the demo-runner test to verify it fails**

Run: `uv run --with pytest pytest /Users/kelton/ai漫剧/ai-manga-studio/tests/test_run_demo.py -v`

Expected: FAIL with `ModuleNotFoundError` for `scripts.run_demo`

- [ ] **Step 3: Implement the runner and create the placeholder still images**

```python
# /Users/kelton/ai漫剧/ai-manga-studio/scripts/run_demo.py
#!/usr/bin/env python3
from argparse import ArgumentParser
from pathlib import Path

from scripts.build_audio import build_project_audio
from scripts.build_shots import normalize_project_shots
from scripts.local_video.project_paths import ProjectPaths
from scripts.render_video import render_project_video


def run_pipeline(paths: ProjectPaths) -> Path:
    normalize_project_shots(paths)
    build_project_audio(paths)
    return render_project_video(paths)


def parse_args() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("--project", default="demo-001")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
    )
    return parser


def main() -> None:
    args = parse_args().parse_args()
    paths = ProjectPaths(repo_root=Path(args.repo_root), project_name=args.project)
    output_path = run_pipeline(paths)
    print(f"Finished demo render: {output_path}")


if __name__ == "__main__":
    main()
```

```bash
mkdir -p /Users/kelton/ai漫剧/ai-manga-studio/storage/projects/demo-001/stills

magick -size 1080x1920 gradient:'#1b0d0a-#5b2718' \
  -fill '#f3dfb6' -gravity north -pointsize 96 -annotate +0+180 '冷宫惊醒' \
  -fill '#e5c793' -gravity south -pointsize 48 -annotate +0+220 '苏晚睁眼，帷帐破旧，寒意透骨' \
  /Users/kelton/ai漫剧/ai-manga-studio/storage/projects/demo-001/stills/shot-001.png

magick -size 1080x1920 gradient:'#140b12-#6a1e35' \
  -fill '#f8e27a' -gravity north -pointsize 96 -annotate +0+180 '系统降临' \
  -fill '#f6d48d' -gravity south -pointsize 48 -annotate +0+220 '金色面板悬在空中，任务只有三日' \
  /Users/kelton/ai漫剧/ai-manga-studio/storage/projects/demo-001/stills/shot-002.png

magick -size 1080x1920 gradient:'#243040-#6f4f35' \
  -fill '#f3e3c4' -gravity north -pointsize 96 -annotate +0+180 '回廊初见' \
  -fill '#dcbf92' -gravity south -pointsize 48 -annotate +0+220 '她抬眼时，回廊尽头那人已停下脚步' \
  /Users/kelton/ai漫剧/ai-manga-studio/storage/projects/demo-001/stills/shot-003.png

magick -size 1080x1920 gradient:'#111317-#3c4350' \
  -fill '#f2dfbe' -gravity north -pointsize 96 -annotate +0+180 '你不是她' \
  -fill '#cab089' -gravity south -pointsize 48 -annotate +0+220 '摄政王声音极轻，却比寒风更冷' \
  /Users/kelton/ai漫剧/ai-manga-studio/storage/projects/demo-001/stills/shot-004.png
```

- [ ] **Step 4: Run the orchestration test and the real smoke render**

Run: `uv run --with pytest pytest /Users/kelton/ai漫剧/ai-manga-studio/tests/test_run_demo.py -v`
Expected: PASS with `1 passed`

Run: `uv run python /Users/kelton/ai漫剧/ai-manga-studio/scripts/run_demo.py --project demo-001`
Expected: `storage/projects/demo-001/audio/*.aiff`, `storage/projects/demo-001/build/subtitles.srt`, `storage/projects/demo-001/build/shot-*.mp4`, and `/Users/kelton/ai漫剧/ai-manga-studio/storage/renders/episode-001.mp4` all exist

Run: `ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 /Users/kelton/ai漫剧/ai-manga-studio/storage/renders/episode-001.mp4`
Expected: prints a duration between `20` and `30` seconds

- [ ] **Step 5: Commit the runner and demo stills**

```bash
git -C /Users/kelton/ai漫剧/ai-manga-studio add \
  scripts/run_demo.py \
  storage/projects/demo-001/stills/shot-001.png \
  storage/projects/demo-001/stills/shot-002.png \
  storage/projects/demo-001/stills/shot-003.png \
  storage/projects/demo-001/stills/shot-004.png \
  tests/test_run_demo.py
git -C /Users/kelton/ai漫剧/ai-manga-studio commit -m "feat: add local demo runner and still assets"
```
