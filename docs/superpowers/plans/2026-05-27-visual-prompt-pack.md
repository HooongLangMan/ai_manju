# Visual Prompt Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local prompt pack generator that turns fixed character/style data and demo shot metadata into per-shot image prompts.

**Architecture:** Keep this as a sidecar to the existing render pipeline. Add prompt-specific helpers under `scripts/local_video/`, a thin CLI entry point in `scripts/build_prompts.py`, and project-authored visual files under `storage/projects/demo-001/`. Existing audio and render scripts should continue to treat prompt fields as metadata.

**Tech Stack:** Python standard library, `uv`, `pytest`, JSON, Markdown

---

## File Structure

- Modify: `scripts/local_video/project_paths.py`
  Purpose: expose `characters_file`, `style_guide_file`, and `prompts_dir`.
- Modify: `scripts/local_video/shots.py`
  Purpose: preserve optional `visual_prompt` and `negative_prompt` fields.
- Create: `scripts/local_video/prompts.py`
  Purpose: load character anchors and render/write per-shot prompt Markdown files.
- Create: `scripts/build_prompts.py`
  Purpose: CLI entry point for generating prompt files.
- Create: `storage/projects/demo-001/characters.json`
  Purpose: authored character and motif continuity anchors.
- Create: `storage/projects/demo-001/style_guide.md`
  Purpose: authored global image style rules.
- Modify: `storage/projects/demo-001/shots.json`
  Purpose: add shot-specific visual prompt metadata.
- Create: `tests/test_prompts.py`
  Purpose: cover prompt helper behavior.
- Create: `tests/test_build_prompts.py`
  Purpose: cover CLI-level prompt generation.

## Tasks

- [ ] Task 1: Add prompt path and shot metadata support with failing tests first.
- [ ] Task 2: Add prompt rendering helpers with failing tests first.
- [ ] Task 3: Add CLI and demo authored prompt assets with failing tests first.
- [ ] Task 4: Run full verification, generate prompt files, commit, and push.
