# Local-First Candidate Pool Design

## Goal

Add a local-first image candidate pool so each shot can collect images from local tools, manual downloads, ComfyUI, or later API refinements before one candidate is promoted to the final `stills/shot-xxx.png` used by the renderer.

## Principle

API image generation should be a refinement and fallback layer, not the default bulk producer. The local workflow should make it cheap to try many local candidates, accept good local outputs directly, and spend API calls only on selected shots that need polish.

## Storage Layout

Each project gets a candidate folder and manifest:

```text
storage/projects/demo-001/
  candidates/
    shot-001/
      local-001.png
      api-refine-001.png
    shot-002/
      local-001.png
  asset_manifest.json
  stills/
    shot-001.png
    shot-002.png
```

`candidates/` stores all possible image outputs. `stills/` remains the stable render input. Existing render scripts do not need to know about candidates.

## Manifest

`asset_manifest.json` records candidate and selection state:

```json
{
  "shot-001": {
    "selected": "candidates/shot-001/local-001.png",
    "status": "accepted",
    "notes": "本地图可用，不走 API",
    "candidates": [
      {
        "path": "candidates/shot-001/local-001.png",
        "source": "local",
        "notes": "ComfyUI first pass"
      }
    ]
  }
}
```

The manifest is authored project data and should be committed. Candidate image binaries are generated assets and should stay ignored unless a specific final example needs to be tracked.

## Scripts

`scripts/import_candidate.py`

- copies an existing image into `candidates/<shot>/`
- creates deterministic names such as `local-001.png`, `local-002.png`
- records source and notes in `asset_manifest.json`
- does not change the final still

`scripts/select_still.py`

- validates that the requested candidate belongs to the requested shot
- copies it into `stills/<shot>.png`
- records `selected`, `status`, and notes in `asset_manifest.json`
- lets the existing `scripts/run_demo.py` use the selected image without render changes

## Acceptance Criteria

- A candidate can be imported for `shot-001` without touching `stills/shot-001.png`.
- A candidate can be selected and copied into `stills/shot-001.png`.
- The manifest records candidates and the selected image.
- Existing video rendering still works because final still paths are unchanged.
- No API calls are made in this stage.
