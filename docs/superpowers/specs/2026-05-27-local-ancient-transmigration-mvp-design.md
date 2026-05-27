# Local Ancient Transmigration MVP Design

## Goal

Build a small local workflow that can render one 20-30 second "ancient costume transmigration system" short video from structured shot data, static still images, local TTS, subtitles, and `ffmpeg`.

## Scope

This MVP is intentionally narrow. It exists to prove that the local production chain works end to end:

`story.md -> shots.json -> TTS audio -> subtitles -> ffmpeg render -> mp4`

The first output is one demo episode with four shots, one line of dialogue per shot, and one final `mp4`.

## Non-Goals

The MVP does not include:

- knowledge graph extraction
- character turnaround generation
- ComfyUI automation
- image-to-video generation
- a web UI
- a FastAPI service
- shared package abstractions
- scene-level background music mixing
- automatic LLM shot breakdown

## Repository Boundaries

The current repository is a skeleton. For the MVP, we use only the folders that directly help us render one local demo:

- `storage/projects/demo-001/`
  Holds story input, shot data, still images, generated audio, and per-project build artifacts.
- `storage/renders/`
  Holds the final rendered episode output.
- `scripts/`
  Holds the local workflow scripts.

The first MVP does not touch `apps/web`, `apps/api`, or `packages/shared`.

## Project Layout

The demo project will use this structure:

```text
storage/projects/demo-001/
  story.md
  shots.json
  stills/
    shot-001.png
    shot-002.png
    shot-003.png
    shot-004.png
  audio/
    shot-001.aiff
    shot-002.aiff
    shot-003.aiff
    shot-004.aiff
  build/
    durations.json
    subtitles.srt
    shot-001.mp4
    shot-002.mp4
    shot-003.mp4
    shot-004.mp4

storage/renders/
  episode-001.mp4
```

## Demo Story

The first demo episode uses a four-shot structure:

1. Su Wan wakes in a cold palace room and realizes she has transmigrated.
2. A gold system prompt appears and gives her a three-day mission to approach the regent prince.
3. She meets the regent prince in a covered corridor for the first time.
4. The regent prince says, "You are not her," and the clip ends on that hook.

This story is short enough for a first render but already tests atmosphere, subtitles, voice, timing, and hook-based pacing.

## Data Model

`storage/projects/demo-001/shots.json` is the single source of truth for renderable shot data. The MVP keeps the schema intentionally small:

```json
[
  {
    "id": "shot-001",
    "image": "stills/shot-001.png",
    "duration_sec": 6,
    "camera_motion": "slow_push_in",
    "voice": "female_narrator",
    "dialogue": "I was supposed to die on the operating table. Where is this place?",
    "subtitle": "I was supposed to die on the operating table. Where is this place?"
  }
]
```

Required fields:

- `id`: stable shot identifier, for example `shot-001`
- `image`: project-relative still image path
- `duration_sec`: minimum intended shot duration
- `camera_motion`: one of `static`, `slow_push_in`, `slow_pan_left`, `slow_pan_right`
- `voice`: TTS voice key used by the audio builder
- `dialogue`: source text for TTS
- `subtitle`: text written to the subtitle file

Deferred fields:

- `transition`
- `sfx`
- `music`
- multi-speaker timing data
- prompt metadata

Those fields stay out of the first schema because they are not required to render the first working video.

## Script Responsibilities

The workflow is split into three focused scripts plus one small entry point.

### `scripts/build_shots.py`

Responsibilities:

- read `storage/projects/<project>/story.md` as the narrative reference for the demo
- read the existing `shots.json`
- validate that every shot includes the required fields
- normalize paths and fill safe defaults
- write the canonical `shots.json`

MVP rule:

- the first MVP treats `shots.json` as a manually authored input file
- this script acts as a validator and normalizer, not a story parser
- if `shots.json` does not exist, the script fails with a clear error that tells the user to create it first

### `scripts/build_audio.py`

Responsibilities:

- read `shots.json`
- generate one TTS file per shot with macOS `say`
- write files to `storage/projects/<project>/audio/`
- measure each audio file duration
- write `storage/projects/<project>/build/durations.json`

MVP rule:

- use the local `say` command first
- use stable voice names mapped from shot `voice` values
- fail clearly if `say` is unavailable or a requested voice is unknown

### `scripts/render_video.py`

Responsibilities:

- read `shots.json`
- read `durations.json`
- compute final shot durations
- generate `subtitles.srt`
- create one temporary `mp4` per shot with `ffmpeg`
- concatenate temporary clips into `storage/renders/episode-001.mp4`

MVP timing rule:

- final shot duration = `max(duration_sec, audio_duration + 0.6)`

That buffer keeps subtitle and audio tails from being cut off.

### `scripts/run_demo.py`

Responsibilities:

- run the three steps in order
- target the default project `demo-001`
- stop immediately if any step fails

This script exists for convenience only. The render logic stays in the three focused scripts above.

## Local Render Pipeline

The first render path is:

```text
story.md
-> scripts/build_shots.py
-> shots.json
-> scripts/build_audio.py
-> audio/*.aiff + build/durations.json
-> scripts/render_video.py
-> build/subtitles.srt + build/shot-*.mp4 + storage/renders/episode-001.mp4
```

Inside `render_video.py`, the pipeline is:

1. Load shot data.
2. Load audio durations.
3. Compute final duration per shot.
4. Apply the configured still-image motion with `ffmpeg`.
5. Attach the shot audio.
6. Generate one project subtitle file.
7. Render temporary shot clips.
8. Concatenate the clips into one final episode file.

## `ffmpeg` Motion Rules

The MVP supports only four motion presets:

- `static`
- `slow_push_in`
- `slow_pan_left`
- `slow_pan_right`

These are enough to make static stills feel alive without turning the renderer into a full camera engine. The implementation should keep the output simple and predictable:

- output format: `mp4`
- target size: `1080x1920`
- target fps: `24`
- audio codec: AAC
- video codec: H.264

## Subtitle Rules

Subtitles are generated directly from the shot order. Each shot contributes one subtitle block:

- start time: shot start time in the final timeline
- end time: shot end time in the final timeline
- text: shot `subtitle`

The subtitle file lives at:

`storage/projects/demo-001/build/subtitles.srt`

The first renderer can burn subtitles into the video during render instead of shipping them as a sidecar file.

## Error Handling

The scripts should fail with direct, local-actionable errors:

- missing `story.md`
- missing `shots.json`
- missing still image file
- invalid `camera_motion`
- TTS generation failure
- `ffmpeg` command failure

The first version should stop at the first failure rather than attempting partial recovery.

## Acceptance Criteria

The MVP is successful when all of the following are true:

- `scripts/run_demo.py` can render the demo project locally
- the render completes without manual editing during the run
- the final file exists at `storage/renders/episode-001.mp4`
- the video contains four sequential shots
- each shot has audible TTS
- subtitles appear for every spoken line
- no shot cuts off dialogue before the audio finishes

## Future Extensions

Once this local MVP works, the next layers can be added without changing the core project shape:

- replace hand-prepared stills with ComfyUI-generated stills
- replace `say` with a higher-quality TTS provider
- add transition and sound-effect fields to `shots.json`
- add an API layer that drives the same project directory format
- move from local providers to SaaS providers while keeping the same shot schema
