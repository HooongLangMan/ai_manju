import json
from pathlib import Path

from scripts.comfy_generate import generate_project_candidate
from scripts.local_video.comfyui import (
    ComfyUIClient,
    ComfyUIOutputImage,
    ComfyUIStructuralError,
    ComfyUITransientError,
    build_flux_schnell_prompt,
    project_prompt_to_flux_text,
)
from scripts.local_video.project_paths import ProjectPaths


class FakeComfyUIClient:
    def __init__(self, output_image: Path) -> None:
        self.output_image = output_image
        self.submitted_prompt: dict | None = None

    def queue_prompt(self, prompt: dict) -> str:
        self.submitted_prompt = prompt
        return "prompt-001"

    def wait_for_output_images(self, prompt_id: str) -> list[ComfyUIOutputImage]:
        assert prompt_id == "prompt-001"
        return [
            ComfyUIOutputImage(
                filename=self.output_image.name,
                subfolder="",
                type="output",
            )
        ]

    def output_image_path(self, image: ComfyUIOutputImage) -> Path:
        return self.output_image


def test_project_prompt_to_flux_text_extracts_useful_sections() -> None:
    prompt_markdown = """
    # shot-001

    ## Global Style

    vertical manhua palace style

    ## Character Anchors

    - 苏晚: young woman in pale blue hanfu

    ## Shot Composition

    冷宫惊醒，月光照在脸上。

    ## Negative Prompt

    modern hospital, watermark
    """.strip()

    flux_text = project_prompt_to_flux_text(prompt_markdown)

    assert "vertical manhua palace style" in flux_text
    assert "young woman in pale blue hanfu" in flux_text
    assert "冷宫惊醒" in flux_text
    assert "Avoid: modern hospital, watermark" in flux_text
    assert "No readable text" in flux_text


def test_build_flux_schnell_prompt_uses_checkpoint_and_vertical_size() -> None:
    prompt = build_flux_schnell_prompt(
        text="ancient palace manhua",
        checkpoint_name="flux1-schnell-fp8.safetensors",
        width=576,
        height=1024,
        seed=527002,
        steps=4,
        filename_prefix="ai_manga_demo_shot_001_flux_schnell",
    )

    assert prompt["30"]["inputs"]["ckpt_name"] == "flux1-schnell-fp8.safetensors"
    assert prompt["27"]["inputs"] == {"width": 576, "height": 1024, "batch_size": 1}
    assert prompt["31"]["inputs"]["seed"] == 527002
    assert prompt["31"]["inputs"]["steps"] == 4
    assert prompt["31"]["inputs"]["cfg"] == 1.0
    assert prompt["9"]["inputs"]["filename_prefix"] == "ai_manga_demo_shot_001_flux_schnell"


def test_generate_project_candidate_queues_comfyui_and_imports_candidate(tmp_path: Path) -> None:
    paths = ProjectPaths(repo_root=tmp_path, project_name="demo-001")
    prompt_dir = paths.prompts_dir
    prompt_dir.mkdir(parents=True)
    (prompt_dir / "shot-001.md").write_text(
        """
        ## Global Style

        vertical manhua palace style

        ## Shot Composition

        cold palace wake up
        """.strip(),
        encoding="utf-8",
    )
    comfy_output = tmp_path / "comfy-output.png"
    comfy_output.write_bytes(b"generated image")
    client = FakeComfyUIClient(comfy_output)

    imported = generate_project_candidate(
        paths=paths,
        shot_id="shot-001",
        client=client,
        seed=527002,
    )

    assert imported == paths.candidates_dir / "shot-001" / "comfyui-001.png"
    assert imported.read_bytes() == b"generated image"
    assert client.submitted_prompt is not None
    assert "vertical manhua palace style" in client.submitted_prompt["6"]["inputs"]["text"]
    manifest = json.loads(paths.asset_manifest_file.read_text(encoding="utf-8"))
    assert manifest["shot-001"]["candidates"][0]["path"] == "candidates/shot-001/comfyui-001.png"
    assert manifest["shot-001"]["candidates"][0]["source"] == "comfyui"


def test_comfyui_client_rejects_error_history() -> None:
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

    try:
        client.extract_output_images(history)
    except RuntimeError as exc:
        assert "CheckpointLoaderSimple" in str(exc)
        assert "bad checkpoint" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError")


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

    try:
        client.extract_output_images(history)
    except ComfyUIStructuralError as exc:
        assert "CheckpointLoaderSimple" in str(exc)
    else:
        raise AssertionError("Expected ComfyUIStructuralError")


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

    try:
        client.extract_output_images(history)
    except ComfyUITransientError as exc:
        assert "KSampler" in str(exc)
    else:
        raise AssertionError("Expected ComfyUITransientError")
