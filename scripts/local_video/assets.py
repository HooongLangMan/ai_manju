import json
from pathlib import Path
import shutil

from scripts.local_video.project_paths import ProjectPaths


Manifest = dict[str, dict]


def load_asset_manifest(paths: ProjectPaths) -> Manifest:
    if not paths.asset_manifest_file.exists():
        return {}
    payload = json.loads(paths.asset_manifest_file.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("asset_manifest.json must contain a JSON object")
    return payload


def save_asset_manifest(paths: ProjectPaths, manifest: Manifest) -> None:
    paths.asset_manifest_file.parent.mkdir(parents=True, exist_ok=True)
    paths.asset_manifest_file.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def project_relative(paths: ProjectPaths, path: Path) -> str:
    return path.relative_to(paths.project_dir).as_posix()


def next_candidate_path(paths: ProjectPaths, shot_id: str, source: str, suffix: str) -> Path:
    shot_dir = paths.candidates_dir / shot_id
    index = 1
    while True:
        candidate = shot_dir / f"{source}-{index:03d}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def import_candidate(
    paths: ProjectPaths,
    shot_id: str,
    source_image: Path,
    source: str,
    notes: str,
) -> Path:
    if not source_image.exists():
        raise FileNotFoundError(f"Missing source image: {source_image}")

    suffix = source_image.suffix.lower() or ".png"
    output_path = next_candidate_path(paths, shot_id, source, suffix)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_image, output_path)

    manifest = load_asset_manifest(paths)
    shot_entry = manifest.setdefault(shot_id, {})
    candidates = shot_entry.setdefault("candidates", [])
    candidates.append(
        {
            "path": project_relative(paths, output_path),
            "source": source,
            "notes": notes,
        }
    )
    save_asset_manifest(paths, manifest)
    return output_path


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


def normalize_candidate_path(paths: ProjectPaths, candidate_path: Path) -> Path:
    if candidate_path.is_absolute():
        return candidate_path
    return paths.project_dir / candidate_path


def select_candidate(
    paths: ProjectPaths,
    shot_id: str,
    candidate_path: Path,
    status: str,
    notes: str,
) -> Path:
    absolute_candidate = normalize_candidate_path(paths, candidate_path)
    expected_dir = paths.candidates_dir / shot_id
    try:
        absolute_candidate.relative_to(expected_dir)
    except ValueError as exc:
        raise ValueError(f"Candidate {absolute_candidate} does not belong to {shot_id}") from exc
    if not absolute_candidate.exists():
        raise FileNotFoundError(f"Missing candidate image: {absolute_candidate}")

    paths.stills_dir.mkdir(parents=True, exist_ok=True)
    final_still = paths.stills_dir / f"{shot_id}.png"
    shutil.copyfile(absolute_candidate, final_still)

    manifest = load_asset_manifest(paths)
    shot_entry = manifest.setdefault(shot_id, {})
    shot_entry["selected"] = project_relative(paths, absolute_candidate)
    shot_entry["status"] = status
    shot_entry["notes"] = notes
    shot_entry.setdefault("candidates", [])
    save_asset_manifest(paths, manifest)
    return final_still
