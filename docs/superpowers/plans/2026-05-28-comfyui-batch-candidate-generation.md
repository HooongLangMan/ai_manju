# ComfyUI Batch Candidate Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the current one-shot ComfyUI bridge into a batch-capable local candidate generator that supports `--shot` and `--project`, fills each shot before moving on, and optionally clears prior ComfyUI candidates for the target scope.

**Architecture:** Keep ComfyUI provider logic in `scripts/local_video/comfyui.py`, add orchestration in a new `scripts/local_video/comfy_batch.py`, and keep `scripts/comfy_generate.py` as a thin CLI router. Reuse the existing candidate pool and manifest so still selection and video rendering stay unchanged.

**Tech Stack:** Python standard library, `uv`, `pytest`, JSON, Markdown, ComfyUI HTTP API

---

## File Structure

- Modify: `scripts/local_video/comfyui.py`
  Purpose: classify structural versus transient generation failures with explicit exception types.
- Modify: `scripts/local_video/assets.py`
  Purpose: add source-scoped candidate cleanup helpers that only remove targeted ComfyUI candidates.
- Create: `scripts/local_video/comfy_batch.py`
  Purpose: orchestrate single-shot and project-wide batch generation, retries, replacement, and run summaries.
- Modify: `scripts/comfy_generate.py`
  Purpose: parse new CLI options and delegate to the batch orchestration layer.
- Modify: `README.md`
  Purpose: document the new single-shot and project batch commands.
- Modify: `tests/test_assets.py`
  Purpose: cover source-specific candidate cleanup.
- Modify: `tests/test_comfyui.py`
  Purpose: cover typed ComfyUI failure classification.
- Create: `tests/test_comfy_batch.py`
  Purpose: cover batch orchestration, retry behavior, replacement behavior, and project routing.
- Create: `tests/test_comfy_generate.py`
  Purpose: keep CLI tests light and focused on argument routing.

## Tasks

### Task 1: Add typed ComfyUI errors and source-scoped candidate cleanup

**Files:**
- Modify: `scripts/local_video/comfyui.py`
- Modify: `scripts/local_video/assets.py`
- Modify: `tests/test_comfyui.py`
- Modify: `tests/test_assets.py`

- [ ] **Step 1: Write the failing source-cleanup test**

```python
def test_remove_candidates_by_source_only_removes_matching_source(tmp_path: Path) -> None:
    paths = ProjectPaths(repo_root=tmp_path, project_name="demo-001")
    comfy_source = tmp_path / "comfy.png"
    local_source = tmp_path / "local.png"
    comfy_source.write_bytes(b"comfy")
    local_source.write_bytes(b"local")

    comfy_imported = import_candidate(
        paths=paths,
        shot_id="shot-001",
        source_image=comfy_source,
        source="comfyui",
        notes="remove me",
    )
    local_imported = import_candidate(
        paths=paths,
        shot_id="shot-001",
        source_image=local_source,
        source="local",
        notes="keep me",
    )

    removed = remove_candidates_by_source(paths, "shot-001", "comfyui")

    assert removed == [comfy_imported]
    assert not comfy_imported.exists()
    assert local_imported.exists()
    manifest = json.loads(paths.asset_manifest_file.read_text(encoding="utf-8"))
    assert manifest["shot-001"]["candidates"] == [
        {
            "path": "candidates/shot-001/local-001.png",
            "source": "local",
            "notes": "keep me",
        }
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --with pytest pytest tests/test_assets.py::test_remove_candidates_by_source_only_removes_matching_source -q`

Expected: FAIL with `ImportError` or `NameError` because `remove_candidates_by_source` does not exist yet.

- [ ] **Step 3: Write the minimal cleanup helper**

```python
def remove_candidates_by_source(
    paths: ProjectPaths,
    shot_id: str,
    source: str,
) -> list[Path]:
    manifest = load_asset_manifest(paths)
    shot_entry = manifest.get(shot_id)
    if not shot_entry:
        return []

    removed: list[Path] = []
    remaining: list[dict] = []
    for candidate in shot_entry.get("candidates", []):
        if candidate.get("source") != source:
            remaining.append(candidate)
            continue
        candidate_path = normalize_candidate_path(paths, Path(candidate["path"]))
        if candidate_path.exists():
            candidate_path.unlink()
        removed.append(candidate_path)

    shot_entry["candidates"] = remaining
    manifest[shot_id] = shot_entry
    save_asset_manifest(paths, manifest)
    return removed
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --with pytest pytest tests/test_assets.py::test_remove_candidates_by_source_only_removes_matching_source -q`

Expected: PASS

- [ ] **Step 5: Write the failing ComfyUI error-classification tests**

```python
def test_comfyui_client_classifies_checkpoint_errors_as_structural() -> None:
    client = ComfyUIClient(output_dir=Path("/tmp"))
    history = {
        "status": {
            "status_str": "error",
            "messages": [
                [
                    "execution_error",
                    {
                        "node_type": "CheckpointLoaderSimple",
                        "exception_message": "bad checkpoint",
                    },
                ]
            ],
        }
    }

    with pytest.raises(ComfyUIStructuralError, match="CheckpointLoaderSimple"):
        client.extract_output_images(history)


def test_comfyui_client_classifies_sampler_errors_as_transient() -> None:
    client = ComfyUIClient(output_dir=Path("/tmp"))
    history = {
        "status": {
            "status_str": "error",
            "messages": [
                [
                    "execution_error",
                    {
                        "node_type": "KSampler",
                        "exception_message": "temporary sampler failure",
                    },
                ]
            ],
        }
    }

    with pytest.raises(ComfyUITransientError, match="KSampler"):
        client.extract_output_images(history)
```

- [ ] **Step 6: Run tests to verify they fail**

Run: `uv run --with pytest pytest tests/test_comfyui.py::test_comfyui_client_classifies_checkpoint_errors_as_structural tests/test_comfyui.py::test_comfyui_client_classifies_sampler_errors_as_transient -q`

Expected: FAIL because `ComfyUIStructuralError` and `ComfyUITransientError` do not exist yet.

- [ ] **Step 7: Add explicit ComfyUI exception types and routing**

```python
class ComfyUIError(RuntimeError):
    pass


class ComfyUIStructuralError(ComfyUIError):
    pass


class ComfyUITransientError(ComfyUIError):
    pass


def wait_for_output_images(self, prompt_id: str) -> list[ComfyUIOutputImage]:
    deadline = time.monotonic() + self.timeout_sec
    while time.monotonic() < deadline:
        history = self._json_request(f"/history/{prompt_id}")
        if prompt_id in history:
            return self.extract_output_images(history[prompt_id])
        time.sleep(self.poll_interval_sec)
    raise ComfyUITransientError(f"ComfyUI prompt timed out: {prompt_id}")


def extract_output_images(self, history_item: dict) -> list[ComfyUIOutputImage]:
    status = history_item.get("status", {})
    if status.get("status_str") == "error":
        message = _format_comfyui_error(status)
        if "CheckpointLoaderSimple" in message:
            raise ComfyUIStructuralError(message)
        raise ComfyUITransientError(message)
    images: list[ComfyUIOutputImage] = []
    for output in history_item.get("outputs", {}).values():
        for image in output.get("images", []):
            images.append(
                ComfyUIOutputImage(
                    filename=str(image["filename"]),
                    subfolder=str(image.get("subfolder", "")),
                    type=str(image.get("type", "output")),
                )
            )
    if not images:
        raise ComfyUIStructuralError("ComfyUI finished but returned no output images")
    return images
```

- [ ] **Step 8: Run focused tests to verify they pass**

Run: `uv run --with pytest pytest tests/test_assets.py tests/test_comfyui.py -q`

Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add scripts/local_video/assets.py scripts/local_video/comfyui.py tests/test_assets.py tests/test_comfyui.py
git commit -m "feat: add comfyui cleanup and error helpers"
```

### Task 2: Add batch orchestration for single-shot and project-wide generation

**Files:**
- Create: `scripts/local_video/comfy_batch.py`
- Create: `tests/test_comfy_batch.py`

- [ ] **Step 1: Write the failing orchestration tests**

```python
def test_generate_candidates_for_shot_retries_until_variants_are_filled(tmp_path: Path) -> None:
    paths = ProjectPaths(repo_root=tmp_path, project_name="demo-001")
    paths.prompts_dir.mkdir(parents=True)
    (paths.prompts_dir / "shot-001.md").write_text("## Global Style\n\nvertical manhua", encoding="utf-8")

    calls: list[tuple[str, int]] = []
    failures = iter([ComfyUITransientError("temporary"), None, None])

    def fake_generate_one(**kwargs) -> Path:
        calls.append((kwargs["shot_id"], kwargs["seed"]))
        result = next(failures)
        if result is not None:
            raise result
        output = tmp_path / f"{len(calls)}.png"
        output.write_bytes(b"image")
        return import_candidate(
            paths=kwargs["paths"],
            shot_id=kwargs["shot_id"],
            source_image=output,
            source="comfyui",
            notes=f"seed {kwargs['seed']}",
        )

    summary = generate_candidates_for_shot(
        paths=paths,
        shot_id="shot-001",
        client=object(),
        variants=2,
        max_attempts_per_image=20,
        generate_one=fake_generate_one,
    )

    assert len(summary.created_paths) == 2
    assert summary.retries_used == 1


def test_generate_candidates_for_project_waits_for_current_shot_before_next(tmp_path: Path) -> None:
    paths = ProjectPaths(repo_root=tmp_path, project_name="demo-001")
    paths.project_dir.mkdir(parents=True)
    dump_shots(
        paths.shots_file,
        [
            Shot(
                id="shot-001",
                image="stills/shot-001.png",
                duration_sec=1.0,
                camera_motion="static",
                voice="narrator",
                dialogue="a",
                subtitle="a",
            ),
            Shot(
                id="shot-002",
                image="stills/shot-002.png",
                duration_sec=1.0,
                camera_motion="static",
                voice="narrator",
                dialogue="b",
                subtitle="b",
            ),
        ],
    )
    order: list[str] = []

    def fake_generate_shot(**kwargs) -> ShotBatchSummary:
        order.append(kwargs["shot_id"])
        return ShotBatchSummary(shot_id=kwargs["shot_id"], created_paths=[], retries_used=0)

    generate_candidates_for_project(
        paths=paths,
        client=object(),
        variants=2,
        generate_shot=fake_generate_shot,
    )

    assert order == ["shot-001", "shot-002"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest pytest tests/test_comfy_batch.py -q`

Expected: FAIL with `ModuleNotFoundError` because `scripts.local_video.comfy_batch` does not exist yet.

- [ ] **Step 3: Write the minimal batch orchestration module**

```python
@dataclass(frozen=True)
class ShotBatchSummary:
    shot_id: str
    created_paths: list[Path]
    retries_used: int


@dataclass(frozen=True)
class BatchRunSummary:
    mode: str
    shot_summaries: list[ShotBatchSummary]
    replace_source: str | None


def generate_shot_candidate(
    paths: ProjectPaths,
    shot_id: str,
    client: ComfyUIClient,
    checkpoint_name: str,
    width: int,
    height: int,
    seed: int,
    steps: int,
) -> Path:
    prompt_path = paths.prompts_dir / f"{shot_id}.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Missing prompt file: {prompt_path}")
    prompt_text = project_prompt_to_flux_text(prompt_path.read_text(encoding="utf-8"))
    workflow = build_flux_schnell_prompt(
        text=prompt_text,
        checkpoint_name=checkpoint_name,
        width=width,
        height=height,
        seed=seed,
        steps=steps,
        filename_prefix=f"ai_manga_{paths.project_name}_{shot_id}_flux_schnell",
    )
    prompt_id = client.queue_prompt(workflow)
    outputs = client.wait_for_output_images(prompt_id)
    output_image = client.output_image_path(outputs[0])
    return import_candidate(
        paths=paths,
        shot_id=shot_id,
        source_image=output_image,
        source="comfyui",
        notes=f"ComfyUI {checkpoint_name}, seed {seed}, {width}x{height}, {steps} steps",
    )


def generate_candidates_for_shot(
    paths: ProjectPaths,
    shot_id: str,
    client: ComfyUIClient,
    variants: int,
    replace_source: str | None = None,
    checkpoint_name: str = "flux1-schnell-fp8.safetensors",
    width: int = 576,
    height: int = 1024,
    seed: int = 527002,
    steps: int = 4,
    max_attempts_per_image: int = 20,
    generate_one: Callable | None = None,
) -> ShotBatchSummary:
    generator = generate_one or generate_shot_candidate
    if replace_source == "comfyui":
        remove_candidates_by_source(paths, shot_id, "comfyui")
    created: list[Path] = []
    retries_used = 0
    for slot_index in range(variants):
        attempts = 0
        while True:
            attempts += 1
            current_seed = seed + slot_index + retries_used
            try:
                created.append(
                    generator(
                        paths=paths,
                        shot_id=shot_id,
                        client=client,
                        checkpoint_name=checkpoint_name,
                        width=width,
                        height=height,
                        seed=current_seed,
                        steps=steps,
                    )
                )
                break
            except ComfyUITransientError:
                retries_used += 1
                if attempts >= max_attempts_per_image:
                    raise
    return ShotBatchSummary(shot_id=shot_id, created_paths=created, retries_used=retries_used)


def generate_candidates_for_project(
    paths: ProjectPaths,
    client: ComfyUIClient,
    variants: int,
    replace_source: str | None = None,
    checkpoint_name: str = "flux1-schnell-fp8.safetensors",
    width: int = 576,
    height: int = 1024,
    seed: int = 527002,
    steps: int = 4,
    max_attempts_per_image: int = 20,
    generate_shot: Callable | None = None,
) -> BatchRunSummary:
    shots = load_shots(paths.shots_file)
    generator = generate_shot or generate_candidates_for_shot
    summaries = [
        generator(
            paths=paths,
            shot_id=shot.id,
            client=client,
            variants=variants,
            replace_source=replace_source,
            checkpoint_name=checkpoint_name,
            width=width,
            height=height,
            seed=seed + index * 1000,
            steps=steps,
            max_attempts_per_image=max_attempts_per_image,
        )
        for index, shot in enumerate(shots)
    ]
    return BatchRunSummary(mode="project", shot_summaries=summaries, replace_source=replace_source)
```

- [ ] **Step 4: Run focused tests to verify they pass**

Run: `uv run --with pytest pytest tests/test_comfy_batch.py -q`

Expected: PASS

- [ ] **Step 5: Add the failing structural-stop test**

```python
def test_generate_candidates_for_shot_stops_on_missing_prompt(tmp_path: Path) -> None:
    paths = ProjectPaths(repo_root=tmp_path, project_name="demo-001")

    with pytest.raises(FileNotFoundError, match="Missing prompt file"):
        generate_candidates_for_shot(
            paths=paths,
            shot_id="shot-001",
            client=object(),
            variants=2,
        )
```

- [ ] **Step 6: Run the focused structural-stop test**

Run: `uv run --with pytest pytest tests/test_comfy_batch.py::test_generate_candidates_for_shot_stops_on_missing_prompt -q`

Expected: PASS with the current implementation because missing prompts are structural failures that should stop the run.

- [ ] **Step 7: Commit**

```bash
git add scripts/local_video/comfy_batch.py tests/test_comfy_batch.py
git commit -m "feat: add comfyui batch orchestration"
```

### Task 3: Expand the CLI to route `--shot`, `--project`, `--variants`, and replacement mode

**Files:**
- Modify: `scripts/comfy_generate.py`
- Create: `tests/test_comfy_generate.py`
- Modify: `README.md`

- [ ] **Step 1: Write the failing CLI routing tests**

```python
def test_run_generation_routes_to_single_shot(monkeypatch, tmp_path: Path) -> None:
    calls: list[tuple[str, str, int, str | None]] = []

    class FakeClient:
        def __init__(self, **kwargs) -> None:
            pass

    def fake_generate_for_shot(**kwargs):
        calls.append(("shot", kwargs["shot_id"], kwargs["variants"], kwargs["replace_source"]))
        return ShotBatchSummary(shot_id=kwargs["shot_id"], created_paths=[], retries_used=0)

    monkeypatch.setattr("scripts.comfy_generate.ComfyUIClient", FakeClient)
    monkeypatch.setattr("scripts.comfy_generate.generate_candidates_for_shot", fake_generate_for_shot)

    args = parse_args().parse_args(["--project", "demo-001", "--shot", "shot-001"])
    run_generation(args)

    assert calls == [("shot", "shot-001", 2, None)]


def test_run_generation_routes_to_project_mode(monkeypatch) -> None:
    calls: list[tuple[str, int, str | None]] = []

    class FakeClient:
        def __init__(self, **kwargs) -> None:
            pass

    def fake_generate_for_project(**kwargs):
        calls.append(("project", kwargs["variants"], kwargs["replace_source"]))
        return BatchRunSummary(mode="project", shot_summaries=[], replace_source=kwargs["replace_source"])

    monkeypatch.setattr("scripts.comfy_generate.ComfyUIClient", FakeClient)
    monkeypatch.setattr("scripts.comfy_generate.generate_candidates_for_project", fake_generate_for_project)

    args = parse_args().parse_args(["--project", "demo-001", "--replace-source", "comfyui"])
    run_generation(args)

    assert calls == [("project", 2, "comfyui")]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --with pytest pytest tests/test_comfy_generate.py -q`

Expected: FAIL because `run_generation` and the new routing imports do not exist yet.

- [ ] **Step 3: Refactor the CLI into a thin router**

```python
from scripts.local_video.comfy_batch import (
    BatchRunSummary,
    ShotBatchSummary,
    generate_candidates_for_project,
    generate_candidates_for_shot,
)


def run_generation(args) -> BatchRunSummary | ShotBatchSummary:
    paths = ProjectPaths(repo_root=Path(args.repo_root), project_name=args.project)
    client = ComfyUIClient(
        base_url=args.base_url,
        output_dir=Path(args.output_dir),
    )
    if args.shot:
        return generate_candidates_for_shot(
            paths=paths,
            shot_id=args.shot,
            client=client,
            variants=args.variants,
            replace_source=args.replace_source,
            checkpoint_name=args.checkpoint,
            width=args.width,
            height=args.height,
            seed=args.seed,
            steps=args.steps,
            max_attempts_per_image=args.max_attempts_per_image,
        )
    return generate_candidates_for_project(
        paths=paths,
        client=client,
        variants=args.variants,
        replace_source=args.replace_source,
        checkpoint_name=args.checkpoint,
        width=args.width,
        height=args.height,
        seed=args.seed,
        steps=args.steps,
        max_attempts_per_image=args.max_attempts_per_image,
    )


def parse_args() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("--project", default="demo-001")
    parser.add_argument("--shot")
    parser.add_argument("--variants", type=int, default=2)
    parser.add_argument("--replace-source", choices=["comfyui"])
    parser.add_argument("--max-attempts-per-image", type=int, default=20)
    parser.add_argument("--base-url", default="http://127.0.0.1:8188")
    parser.add_argument("--output-dir", default="/Users/kelton/ai漫剧/ComfyUI/output")
    parser.add_argument("--checkpoint", default="flux1-schnell-fp8.safetensors")
    parser.add_argument("--width", type=int, default=576)
    parser.add_argument("--height", type=int, default=1024)
    parser.add_argument("--seed", type=int, default=527002)
    parser.add_argument("--steps", type=int, default=4)
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
    )
    return parser
```

- [ ] **Step 4: Update README usage examples**

```md
## Local ComfyUI Candidate

Single-shot candidate generation:

```bash
uv run python scripts/comfy_generate.py --project demo-001 --shot shot-001 --variants 2
```

Project-wide candidate generation:

```bash
uv run python scripts/comfy_generate.py --project demo-001 --variants 2 --replace-source comfyui
```
```

- [ ] **Step 5: Run focused tests to verify they pass**

Run: `uv run --with pytest pytest tests/test_comfy_generate.py tests/test_comfy_batch.py tests/test_assets.py tests/test_comfyui.py -q`

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/comfy_generate.py README.md tests/test_comfy_generate.py
git commit -m "feat: add comfyui batch generation cli"
```

### Task 4: Run full verification and perform a real local smoke test

**Files:**
- Modify: none expected
- Verify: `storage/projects/demo-001/build/prompts/*.md`
- Verify: `storage/projects/demo-001/candidates/`

- [ ] **Step 1: Run the full automated test suite**

Run: `uv run --with pytest pytest tests -q`

Expected: PASS with all tests green.

- [ ] **Step 2: Rebuild prompt files for the demo project**

Run: `uv run python scripts/build_prompts.py --project demo-001`

Expected: `Wrote 4 prompt files to /Users/kelton/ai漫剧/ai-manga-studio/storage/projects/demo-001/build/prompts`

- [ ] **Step 3: Run a real single-shot smoke test against the local ComfyUI server**

Run: `uv run python scripts/comfy_generate.py --project demo-001 --shot shot-001 --variants 2 --replace-source comfyui`

Expected: two new `comfyui-*.png` files under `storage/projects/demo-001/candidates/shot-001/` and a concise run summary.

- [ ] **Step 4: Run a real full-project smoke test**

Run: `uv run python scripts/comfy_generate.py --project demo-001 --variants 2 --replace-source comfyui`

Expected: each shot receives two `comfyui-*.png` candidates before the next shot starts, or the command stops with a clear structural error.

- [ ] **Step 5: Inspect manifest results**

Run: `sed -n '1,240p' storage/projects/demo-001/asset_manifest.json`

Expected: only `source == "comfyui"` candidate rows are replaced by the smoke tests; non-ComfyUI rows remain.

- [ ] **Step 6: Commit and push**

```bash
git add scripts/local_video/assets.py scripts/local_video/comfyui.py scripts/local_video/comfy_batch.py scripts/comfy_generate.py README.md tests/test_assets.py tests/test_comfyui.py tests/test_comfy_batch.py tests/test_comfy_generate.py
git commit -m "feat: add comfyui batch candidate generation"
git push origin main
```
