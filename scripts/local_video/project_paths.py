from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    repo_root: Path
    project_name: str
    render_filename: str = "episode-001.mp4"

    @property
    def project_dir(self) -> Path:
        return self.repo_root / "storage" / "projects" / self.project_name

    @property
    def story_file(self) -> Path:
        return self.project_dir / "story.md"

    @property
    def characters_file(self) -> Path:
        return self.project_dir / "characters.json"

    @property
    def style_guide_file(self) -> Path:
        return self.project_dir / "style_guide.md"

    @property
    def shots_file(self) -> Path:
        return self.project_dir / "shots.json"

    @property
    def stills_dir(self) -> Path:
        return self.project_dir / "stills"

    @property
    def audio_dir(self) -> Path:
        return self.project_dir / "audio"

    @property
    def build_dir(self) -> Path:
        return self.project_dir / "build"

    @property
    def prompts_dir(self) -> Path:
        return self.build_dir / "prompts"

    @property
    def durations_file(self) -> Path:
        return self.build_dir / "durations.json"

    @property
    def subtitle_file(self) -> Path:
        return self.build_dir / "subtitles.srt"

    @property
    def render_dir(self) -> Path:
        return self.repo_root / "storage" / "renders"

    @property
    def render_output(self) -> Path:
        return self.render_dir / self.render_filename

    def ensure_generated_dirs(self) -> None:
        for path in (self.audio_dir, self.build_dir, self.prompts_dir, self.render_dir):
            path.mkdir(parents=True, exist_ok=True)
