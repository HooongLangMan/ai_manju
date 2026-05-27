from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Iterable


ALLOWED_CAMERA_MOTIONS = {
    "static",
    "slow_push_in",
    "slow_pan_left",
    "slow_pan_right",
}


@dataclass(frozen=True)
class Shot:
    id: str
    image: str
    duration_sec: float
    camera_motion: str
    voice: str
    dialogue: str
    subtitle: str

    @classmethod
    def from_dict(cls, payload: dict) -> "Shot":
        required = {
            "id",
            "image",
            "duration_sec",
            "camera_motion",
            "voice",
            "dialogue",
            "subtitle",
        }
        missing = sorted(required - payload.keys())
        if missing:
            raise ValueError(f"Missing required shot fields: {', '.join(missing)}")

        camera_motion = str(payload["camera_motion"])
        if camera_motion not in ALLOWED_CAMERA_MOTIONS:
            raise ValueError(f"Invalid camera_motion: {camera_motion}")

        duration_sec = float(payload["duration_sec"])
        if duration_sec <= 0:
            raise ValueError("duration_sec must be greater than 0")

        return cls(
            id=str(payload["id"]),
            image=str(payload["image"]),
            duration_sec=duration_sec,
            camera_motion=camera_motion,
            voice=str(payload["voice"]),
            dialogue=str(payload["dialogue"]),
            subtitle=str(payload["subtitle"]),
        )


def load_shots(path: Path) -> list[Shot]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not payload:
        raise ValueError("shots.json must contain a non-empty list of shots")
    return [Shot.from_dict(item) for item in payload]


def dump_shots(path: Path, shots: Iterable[Shot]) -> None:
    serialized = [asdict(shot) for shot in shots]
    path.write_text(
        json.dumps(serialized, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
