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
