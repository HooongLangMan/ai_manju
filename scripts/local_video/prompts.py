from dataclasses import dataclass
import json
from pathlib import Path

from scripts.local_video.project_paths import ProjectPaths
from scripts.local_video.shots import Shot, load_shots


@dataclass(frozen=True)
class CharacterAnchor:
    id: str
    name: str
    role: str
    prompt: str
    continuity: str

    @classmethod
    def from_dict(cls, payload: dict) -> "CharacterAnchor":
        required = {"id", "name", "role", "prompt", "continuity"}
        missing = sorted(required - payload.keys())
        if missing:
            raise ValueError(f"Missing required character fields: {', '.join(missing)}")
        return cls(
            id=str(payload["id"]),
            name=str(payload["name"]),
            role=str(payload["role"]),
            prompt=str(payload["prompt"]),
            continuity=str(payload["continuity"]),
        )


def load_character_anchors(path: Path) -> list[CharacterAnchor]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not payload:
        raise ValueError("characters.json must contain a non-empty list")
    return [CharacterAnchor.from_dict(item) for item in payload]


def render_shot_prompt(
    shot: Shot,
    style_guide: str,
    character_anchors: list[CharacterAnchor],
) -> str:
    characters = "\n".join(
        [
            f"- {anchor.name} ({anchor.role}, `{anchor.id}`): {anchor.prompt}\n"
            f"  Continuity: {anchor.continuity}"
            for anchor in character_anchors
        ]
    )
    visual_prompt = shot.visual_prompt or shot.subtitle
    negative_prompt = shot.negative_prompt or (
        "low quality, blurry, watermark, logo, unreadable text, modern clothing, "
        "extra fingers, distorted hands, duplicate face"
    )
    return (
        f"# {shot.id}\n\n"
        "## Image Target\n\n"
        "Create a vertical 9:16 cinematic manhua still for an AI short drama.\n\n"
        "## Global Style\n\n"
        f"{style_guide.strip()}\n\n"
        "## Character Anchors\n\n"
        f"{characters}\n\n"
        "## Shot Composition\n\n"
        f"{visual_prompt.strip()}\n\n"
        "## Dialogue Context\n\n"
        f"{shot.subtitle.strip()}\n\n"
        "## Continuity Notes\n\n"
        "Keep character identity, costume, hair, palette, and facial structure consistent "
        "with the anchors. Only include characters described in the shot composition. "
        "Do not add readable Chinese text inside the image; subtitles are added later "
        "by the video renderer.\n\n"
        "## Negative Prompt\n\n"
        f"{negative_prompt.strip()}\n"
    )


def write_project_prompts(paths: ProjectPaths) -> list[Path]:
    if not paths.characters_file.exists():
        raise FileNotFoundError(f"Missing characters.json: {paths.characters_file}")
    if not paths.style_guide_file.exists():
        raise FileNotFoundError(f"Missing style_guide.md: {paths.style_guide_file}")
    if not paths.shots_file.exists():
        raise FileNotFoundError(f"Missing shots.json: {paths.shots_file}")

    paths.prompts_dir.mkdir(parents=True, exist_ok=True)
    anchors = load_character_anchors(paths.characters_file)
    style_guide = paths.style_guide_file.read_text(encoding="utf-8")
    shots = load_shots(paths.shots_file)

    written: list[Path] = []
    for shot in shots:
        output_path = paths.prompts_dir / f"{shot.id}.md"
        output_path.write_text(
            render_shot_prompt(
                shot=shot,
                style_guide=style_guide,
                character_anchors=anchors,
            ),
            encoding="utf-8",
        )
        written.append(output_path)
    return written
