# Visual Prompt Pack Design

## Goal

Add a lightweight visual prompt production step for the local ancient transmigration demo. The step should turn existing shot data, fixed character cards, and a style guide into per-shot image prompts that can be copied into GPT Image, nano banana, ComfyUI, or another image provider.

## Scope

This stage does not call any image API and does not automate ComfyUI. It prepares stable prompt assets so the user can manually generate better stills, replace the current placeholder images, and re-run the existing local video renderer.

The production path becomes:

```text
characters.json + style_guide.md + shots.json
-> scripts/build_prompts.py
-> storage/projects/demo-001/build/prompts/shot-001.md
-> manual image generation
-> storage/projects/demo-001/stills/shot-001.png
-> scripts/run_demo.py
```

## Data Files

`storage/projects/demo-001/characters.json` stores reusable visual anchors:

- `su_wan`: transmigrated heroine
- `regent_prince`: cold regent prince
- `system_panel`: gold system UI motif

Each character includes role, appearance, costume, palette, continuity notes, and provider-friendly prompt fragments.

`storage/projects/demo-001/style_guide.md` stores global look rules:

- vertical 9:16 comic-drama frame
- ancient Chinese palace transmigration tone
- cinematic manhua illustration
- cool moonlit palace atmosphere with gold system accents
- readable composition and no embedded text in the image

## Shot Prompt Fields

`shots.json` gains optional fields:

- `visual_prompt`: shot-specific composition and action
- `negative_prompt`: shot-specific things to avoid

The existing render scripts should continue working if these fields exist. They are metadata for prompt generation, not rendering.

## Script Responsibilities

`scripts/build_prompts.py` should:

- read `characters.json`, `style_guide.md`, and `shots.json`
- validate that the visual files exist
- generate one Markdown prompt file per shot
- write files under `storage/projects/<project>/build/prompts/`
- print a concise summary with the output directory

The script should not overwrite still images and should not call external AI services.

## Prompt Format

Each generated prompt file should include:

- title with the shot id
- image target: 9:16 vertical manhua still
- global style guide excerpt
- relevant character anchors
- shot-specific visual prompt
- continuity notes
- negative prompt

This format is intentionally readable by humans first. Provider automation can parse or transform it later.

## Acceptance Criteria

- `uv run python scripts/build_prompts.py --project demo-001` writes four prompt files.
- Prompt files include fixed character/style anchors plus shot-specific composition.
- Existing `scripts/run_demo.py` still renders the video after prompt metadata is added to `shots.json`.
- Tests cover character loading, prompt rendering, and CLI orchestration.
