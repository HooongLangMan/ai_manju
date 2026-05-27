from dataclasses import dataclass
import json
from pathlib import Path
import time
from urllib import request


@dataclass(frozen=True)
class ComfyUIOutputImage:
    filename: str
    subfolder: str
    type: str


def _section(markdown: str, title: str) -> str:
    marker = f"## {title}"
    start = markdown.find(marker)
    if start == -1:
        return ""
    start += len(marker)
    next_heading = markdown.find("\n## ", start)
    if next_heading == -1:
        return markdown[start:].strip()
    return markdown[start:next_heading].strip()


def project_prompt_to_flux_text(prompt_markdown: str) -> str:
    style = _section(prompt_markdown, "Global Style")
    anchors = _section(prompt_markdown, "Character Anchors")
    composition = _section(prompt_markdown, "Shot Composition")
    continuity = _section(prompt_markdown, "Continuity Notes")
    negative = _section(prompt_markdown, "Negative Prompt")
    parts = [
        "Vertical 9:16 cinematic Chinese manhua illustration for an AI short drama.",
        style,
        anchors,
        composition,
        continuity,
        "No readable text, no subtitles inside the image, no watermark, no logo.",
    ]
    if negative:
        parts.append(f"Avoid: {negative}")
    return " ".join(part for part in parts if part).replace("\n", " ")


def build_flux_schnell_prompt(
    text: str,
    checkpoint_name: str,
    width: int,
    height: int,
    seed: int,
    steps: int,
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
            "inputs": {"clip": ["30", 1], "text": ""},
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
                "cfg": 1.0,
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
        with request.urlopen(req, timeout=30) as response:
            return json.loads(response.read())

    def queue_prompt(self, prompt: dict) -> str:
        response = self._json_request("/prompt", {"prompt": prompt})
        return str(response["prompt_id"])

    def wait_for_output_images(self, prompt_id: str) -> list[ComfyUIOutputImage]:
        deadline = time.monotonic() + self.timeout_sec
        while time.monotonic() < deadline:
            history = self._json_request(f"/history/{prompt_id}")
            if prompt_id in history:
                return self.extract_output_images(history[prompt_id])
            time.sleep(self.poll_interval_sec)
        raise TimeoutError(f"ComfyUI prompt timed out: {prompt_id}")

    def extract_output_images(self, history_item: dict) -> list[ComfyUIOutputImage]:
        status = history_item.get("status", {})
        if status.get("status_str") == "error":
            raise RuntimeError(_format_comfyui_error(status))
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
            raise RuntimeError("ComfyUI finished but returned no output images")
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
