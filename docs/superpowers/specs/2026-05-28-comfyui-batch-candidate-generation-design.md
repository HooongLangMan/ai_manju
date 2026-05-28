# ComfyUI Batch Candidate Generation Design

## Goal

Add a batch-capable local ComfyUI candidate generation step that can run either a single shot or a whole project and automatically import successful outputs into the existing candidate pool.

## Principle

ComfyUI should remain the local visual generation engine, while project orchestration stays in Python scripts. The new work should extend the current single-shot integration into a production-friendly batch flow without changing final still selection or video rendering.

## Scope

This stage expands local image generation from one-shot manual use to repeatable batch use.

The new production path becomes:

```text
shots.json
-> scripts/build_prompts.py
-> storage/projects/demo-001/build/prompts/shot-001.md
-> scripts/comfy_generate.py --shot shot-001
or
-> scripts/comfy_generate.py --project demo-001
-> storage/projects/demo-001/candidates/shot-001/comfyui-001.png
-> asset_manifest.json
-> manual still selection
-> scripts/run_demo.py
```

This stage does not:

- auto-select final stills
- change `stills/`
- add subtitle, TTS, or render behavior
- add async workers or a job queue

## CLI Shape

The existing entry point stays:

`scripts/comfy_generate.py`

It should support both modes:

- `--project demo-001 --shot shot-001`
- `--project demo-001`

Behavior rules:

- If `--shot` is present, only that shot is processed.
- If `--shot` is absent, all shots in the project are processed in shot order.
- `--variants` defaults to `2`.
- Generation appends new candidates by default.
- `--replace-source comfyui` clears only prior ComfyUI candidates for the target shot set before generating this run.

## Module Responsibilities

`scripts/local_video/comfyui.py`

- owns ComfyUI API calls
- owns workflow construction
- owns waiting for history/output images
- stays focused on provider-specific behavior

`scripts/local_video/comfy_batch.py`

- resolves the target shot list
- loops through shots and variants
- handles retry policy
- imports generated images into the candidate pool
- optionally clears prior ComfyUI candidates for the requested scope
- returns a summary of created images and retry counts

`scripts/comfy_generate.py`

- parses CLI arguments
- constructs `ProjectPaths` and `ComfyUIClient`
- dispatches to single-shot or project batch orchestration through the batch module
- prints a concise run summary

## Candidate And Manifest Behavior

The existing candidate pool remains the source of truth.

Each successful generation:

- saves through ComfyUI output as usual
- is imported into `candidates/<shot>/`
- appends one entry to `asset_manifest.json`

No manifest schema change is required. Existing candidate entries remain valid:

```json
{
  "shot-001": {
    "candidates": [
      {
        "path": "candidates/shot-001/comfyui-003.png",
        "source": "comfyui",
        "notes": "ComfyUI flux1-schnell-fp8.safetensors, seed 527100, 576x1024, 4 steps"
      }
    ]
  }
}
```

`--replace-source comfyui` should be intentionally narrow:

- remove only `source == "comfyui"` manifest entries for the targeted shots
- remove only matching `candidates/<shot>/comfyui-*.png` files
- keep non-ComfyUI candidates such as API or manual imports
- keep `selected`, `status`, and top-level shot notes unchanged
- not attempt to repair or change a prior selected still

## Batch Generation Rules

The batch layer should process shots in deterministic order.

For each shot:

- determine the target variant count
- keep generating until the shot reaches the required number of newly created candidates for this run
- only move to the next shot after the current shot is filled

This is a production choice: a missing shot is more damaging than a slow shot.

## Retry Policy

Retry behavior should be high but finite.

- each image slot retries up to `20` times by default
- transient generation failures retry the current image slot
- the batch does not skip ahead to the next shot until the current shot is complete

This keeps project output complete without risking an endless hang in a bad state.

## Structural Error Handling

Some failures should stop the whole run immediately instead of retrying:

- missing prompt file
- ComfyUI server unavailable
- requested checkpoint unavailable
- output image missing after a reported success
- manifest write failure

These indicate a broken environment or broken project state rather than a bad single sample.

## Run Summary

At the end of a successful or partially successful run, the CLI should print a concise summary including:

- project name
- mode: single shot or full project
- shots processed
- images created
- retries used
- whether prior ComfyUI candidates were cleared first

If a structural error stops the run, the CLI should print the failing shot and reason before exiting non-zero.

## Testing

Add focused tests for orchestration behavior without overloading the CLI layer.

`tests/test_comfy_batch.py`

- single-shot mode processes only the requested shot
- project mode walks all shots in order
- `variants=2` imports two candidates per shot
- `replace-source comfyui` clears only prior ComfyUI candidates
- transient failures retry the current image slot and continue until the shot is filled
- the next shot does not start until the current shot reaches the requested variant count
- structural failures stop the whole run

`tests/test_comfyui.py`

- keep existing workflow and error-path coverage

CLI-level tests should remain light and focus on argument routing rather than full orchestration behavior.

## Acceptance Criteria

- `uv run python scripts/comfy_generate.py --project demo-001 --shot shot-001` can generate multiple candidates for one shot.
- `uv run python scripts/comfy_generate.py --project demo-001` can generate two candidates per shot across the demo project.
- Batch generation imports all successful outputs into the existing candidate pool.
- The current shot is filled before the next shot begins.
- `--replace-source comfyui` only clears prior ComfyUI candidates in the targeted shot scope.
- Structural errors stop the run with a clear message.
- Existing still selection and video rendering continue to work without modification.
