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
