from dataclasses import dataclass
import json
from pathlib import Path
import time
from urllib.error import URLError
from urllib import request


@dataclass(frozen=True)
class ComfyUIOutputImage:
    filename: str
    subfolder: str
    type: str


class ComfyUIError(RuntimeError):
    pass


class ComfyUIStructuralError(ComfyUIError):
    pass


class ComfyUITransientError(ComfyUIError):
    pass


def _section(markdown: str, title: str) -> str:
    sections: dict[str, list[str]] = {}
    current_title: str | None = None
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            current_title = stripped[3:].strip()
            sections[current_title] = []
            continue
        if current_title is not None:
            sections[current_title].append(stripped)
    return "\n".join(sections.get(title, [])).strip()


def _normalize_inline_text(text: str) -> str:
    return " ".join(text.replace("\n", " ").split())


def _sanitize_style_text(style_text: str) -> str:
    sanitized = style_text
    replacements = {
        "Chinese ancient-costume transmigration short drama": "ancient palace costume drama",
        "Chinese manhua illustration": "cinematic costume-drama comic illustration",
        "manhua illustration": "cinematic comic illustration",
        "dramatic short-drama pacing": "dramatic scene pacing",
    }
    for source, target in replacements.items():
        sanitized = sanitized.replace(source, target)
    return sanitized


def _clean_anchor_section(anchors_markdown: str) -> str:
    cleaned_lines: list[str] = []
    for line in anchors_markdown.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- "):
            anchor_text = stripped[2:]
            if ": " in anchor_text:
                anchor_text = anchor_text.split(": ", 1)[1]
            cleaned_lines.append(f"- {anchor_text}")
            continue
        cleaned_lines.append(stripped)
    return "\n".join(cleaned_lines).strip()


def _variant_instruction(variant_name: str) -> str:
    if variant_name == "environment":
        return (
            "Use a wider medium shot with a single subject, upper body visible, subject smaller in frame, "
            "show the moonlit window, bed edge, curtains, lamp, and more palace room context, "
            "clear architectural framing, plain blank surfaces, open negative space, and visually quiet corners."
        )
    return (
        "Use a tight close-up portrait with a single subject, chest-up framing, stronger startled facial emotion, "
        "larger subject scale, simple cropped background, plain curtain or window glow only, and visually quiet corners."
    )


def project_prompt_to_flux_text(prompt_markdown: str, variant_name: str = "portrait") -> str:
    style = _sanitize_style_text(
        _normalize_inline_text(_section(prompt_markdown, "Global Style"))
    )
    anchors = _normalize_inline_text(
        _clean_anchor_section(_section(prompt_markdown, "Character Anchors"))
    )
    composition = _normalize_inline_text(
        _section(prompt_markdown, "Model Visual Prompt")
        or _section(prompt_markdown, "Shot Composition")
    )
    continuity = _normalize_inline_text(_section(prompt_markdown, "Continuity Notes"))
    parts = [
        "Vertical 9:16 cinematic ancient-palace comic still for an AI short drama.",
        style,
        anchors,
        composition,
        _variant_instruction(variant_name),
        continuity,
        (
            "Single clean illustration frame, not a poster, book cover, title page, or promo art. "
            "No readable text, no subtitles inside the image, no watermark, no logo, "
            "no signage, no plaque, no hanging board, no hanging scroll, no couplet banner, "
            "no seal, no calligraphy, no Chinese characters, no captions, no speech bubbles, "
            "no interface text, no decorative corner marks, no side labels, no extra people."
        ),
    ]
    return " ".join(part for part in parts if part)


def project_prompt_to_flux_negative_text(prompt_markdown: str) -> str:
    negative = _normalize_inline_text(_section(prompt_markdown, "Negative Prompt"))
    parts = [
        negative,
        (
            "readable text, chinese characters, english letters, calligraphy, handwriting, "
            "subtitle text, captions, speech bubbles, poster typography, book cover layout, "
            "title design, watermark, logo, signature, artist name, red seal, stamp, plaque, "
            "hanging signboard, hanging scroll, wall inscription, banner text, couplet banner, "
            "corner title text, vertical side text, decorative brush words, printed fabric text, "
            "interface text, extra people, crowd"
        ),
        (
            "title text, brush calligraphy, corner text, edge text, seal stamp, logo mark, "
            "poster layout, book cover composition, artist signature"
        ),
    ]
    return ", ".join(part for part in parts if part)


def build_flux_schnell_prompt(
    text: str,
    negative_text: str,
    checkpoint_name: str,
    width: int,
    height: int,
    seed: int,
    steps: int,
    cfg: float,
    filename_prefix: str,
) -> dict:
    return {
        "30": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": checkpoint_name},
        },
        "27": {
            "class_type": "EmptySD3LatentImage",
            "inputs": {"width": width, "height": height, "batch_size": 1},
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["30", 1], "text": text},
        },
        "33": {
            "class_type": "CLIPTextEncode",
            "inputs": {"clip": ["30", 1], "text": negative_text},
        },
        "31": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["30", 0],
                "positive": ["6", 0],
                "negative": ["33", 0],
                "latent_image": ["27", 0],
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
            },
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["31", 0], "vae": ["30", 2]},
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"images": ["8", 0], "filename_prefix": filename_prefix},
        },
    }


def _service_unavailable_error(base_url: str, exc: URLError) -> ComfyUIStructuralError:
    return ComfyUIStructuralError(
        f"ComfyUI service unavailable at {base_url}: {exc.reason}"
    )


class ComfyUIClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8188",
        output_dir: Path = Path("/Users/kelton/ai漫剧/ComfyUI/output"),
        poll_interval_sec: float = 2.0,
        timeout_sec: float = 600.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.output_dir = output_dir
        self.poll_interval_sec = poll_interval_sec
        self.timeout_sec = timeout_sec

    def _json_request(self, path: str, payload: dict | None = None) -> dict:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.base_url}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        try:
            with request.urlopen(req, timeout=30) as response:
                return json.loads(response.read())
        except URLError as exc:
            raise _service_unavailable_error(self.base_url, exc) from exc

    def queue_prompt(self, prompt: dict) -> str:
        try:
            response = self._json_request("/prompt", {"prompt": prompt})
        except URLError as exc:
            raise _service_unavailable_error(self.base_url, exc) from exc
        return str(response["prompt_id"])

    def wait_for_output_images(self, prompt_id: str) -> list[ComfyUIOutputImage]:
        deadline = time.monotonic() + self.timeout_sec
        while time.monotonic() < deadline:
            try:
                history = self._json_request(f"/history/{prompt_id}")
            except URLError as exc:
                raise _service_unavailable_error(self.base_url, exc) from exc
            if prompt_id in history:
                return self.extract_output_images(history[prompt_id])
            time.sleep(self.poll_interval_sec)
        raise ComfyUITransientError(f"ComfyUI prompt timed out: {prompt_id}")

    def extract_output_images(self, history_item: dict) -> list[ComfyUIOutputImage]:
        status = history_item.get("status", {})
        if status.get("status_str") == "error":
            raise _classify_comfyui_error(status)
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

    def output_image_path(self, image: ComfyUIOutputImage) -> Path:
        return self.output_dir / image.subfolder / image.filename


def _format_comfyui_error(status: dict) -> str:
    for kind, payload in status.get("messages", []):
        if kind == "execution_error":
            node_type = payload.get("node_type", "unknown node")
            message = payload.get("exception_message", "unknown error")
            return f"ComfyUI execution failed at {node_type}: {message}"
    return "ComfyUI execution failed"


def _classify_comfyui_error(status: dict) -> ComfyUIError:
    message = _format_comfyui_error(status)
    if "CheckpointLoaderSimple" in message:
        return ComfyUIStructuralError(message)
    return ComfyUITransientError(message)
