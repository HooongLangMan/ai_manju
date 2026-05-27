# Local-First Candidate Pool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local-first candidate image pool and selection workflow for shot stills without calling any paid image API.

**Architecture:** Keep candidates as a sidecar layer under each project. New helper code owns `asset_manifest.json`, candidate naming, image copying, and final still promotion. The render pipeline remains unchanged and continues to read `storage/projects/<project>/stills/shot-xxx.png`.

**Tech Stack:** Python standard library, `uv`, `pytest`, JSON file manifests, filesystem copy operations

---

## File Structure

- Modify: `scripts/local_video/project_paths.py`
  Purpose: expose `candidates_dir` and `asset_manifest_file`.
- Create: `scripts/local_video/assets.py`
  Purpose: load/save manifest data, import candidate image files, and select candidates as final stills.
- Create: `scripts/import_candidate.py`
  Purpose: CLI entry point for adding local/manual/ComfyUI images to the candidate pool.
- Create: `scripts/select_still.py`
  Purpose: CLI entry point for promoting a candidate to `stills/<shot>.png`.
- Create: `storage/projects/demo-001/asset_manifest.json`
  Purpose: committed empty manifest seed for the demo project.
- Modify: `.gitignore`
  Purpose: ignore generated candidate image binaries while allowing `asset_manifest.json` to be tracked.
- Create: `tests/test_assets.py`
  Purpose: test manifest, import, and selection helpers.
- Create: `tests/test_import_candidate.py`
  Purpose: test import CLI wrapper behavior.
- Create: `tests/test_select_still.py`
  Purpose: test selection CLI wrapper behavior.

## Tasks

- [ ] Task 1: Add candidate paths and manifest seed with failing tests first.
- [ ] Task 2: Add asset manifest/import/select helpers with failing tests first.
- [ ] Task 3: Add import and select CLI wrappers with failing tests first.
- [ ] Task 4: Verify full test suite, run a local candidate import/select smoke test, commit, and push.
