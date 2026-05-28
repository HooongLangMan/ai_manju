from scripts.comfy_generate import parse_args, run_generation
from scripts.local_video.comfy_batch import BatchRunSummary, ShotBatchSummary


def test_run_generation_routes_to_single_shot(monkeypatch) -> None:
    calls: list[tuple[str, str, int, str | None]] = []

    class FakeClient:
        def __init__(self, **kwargs) -> None:
            pass

    def fake_generate_for_shot(**kwargs):
        calls.append(
            ("shot", kwargs["shot_id"], kwargs["variants"], kwargs["replace_source"])
        )
        return ShotBatchSummary(
            shot_id=kwargs["shot_id"],
            created_paths=[],
            retries_used=0,
        )

    monkeypatch.setattr("scripts.comfy_generate.ComfyUIClient", FakeClient)
    monkeypatch.setattr(
        "scripts.comfy_generate.generate_candidates_for_shot",
        fake_generate_for_shot,
    )

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
        return BatchRunSummary(
            mode="project",
            shot_summaries=[],
            replace_source=kwargs["replace_source"],
        )

    monkeypatch.setattr("scripts.comfy_generate.ComfyUIClient", FakeClient)
    monkeypatch.setattr(
        "scripts.comfy_generate.generate_candidates_for_project",
        fake_generate_for_project,
    )

    args = parse_args().parse_args(
        ["--project", "demo-001", "--replace-source", "comfyui"]
    )
    run_generation(args)

    assert calls == [("project", 2, "comfyui")]
