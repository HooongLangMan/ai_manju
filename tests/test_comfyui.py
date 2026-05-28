import json
from pathlib import Path
from urllib.error import URLError

from scripts.comfy_generate import generate_project_candidate
from scripts.local_video.comfyui import (
    ComfyUIClient,
    ComfyUIOutputImage,
    ComfyUIStructuralError,
    ComfyUITransientError,
    build_flux_schnell_prompt,
    project_prompt_to_flux_negative_text,
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

    flux_text = project_prompt_to_flux_text(prompt_markdown, variant_name="portrait")

    assert "vertical manhua palace style" in flux_text
    assert "young woman in pale blue hanfu" in flux_text
    assert "冷宫惊醒" in flux_text
    assert "No readable text" in flux_text
    assert "no signage" in flux_text.lower()
    assert "no seal" in flux_text.lower()
    assert "no chinese characters" in flux_text.lower()
    assert "no extra people" in flux_text.lower()
    negative_text = project_prompt_to_flux_negative_text(prompt_markdown)
    assert "modern hospital, watermark" in negative_text


def test_project_prompt_to_flux_text_prefers_model_prompt_and_strips_chinese_labels() -> None:
    prompt_markdown = """
    # shot-001

    ## Global Style

    vertical manhua palace style

    ## Character Anchors

    - 苏晚 (穿越女主, `su_wan`): young woman in pale blue hanfu
      Continuity: keep the same silver hairpin and oval face

    ## Shot Composition

    苏晚在冷宫榻上惊醒，月光照在脸上。

    ## Model Visual Prompt

    young woman waking up on a worn palace bed, half sitting up, cold moonlight on her shocked face
    """.strip()

    flux_text = project_prompt_to_flux_text(prompt_markdown, variant_name="portrait")

    assert "young woman waking up on a worn palace bed" in flux_text
    assert "young woman in pale blue hanfu" in flux_text
    assert "keep the same silver hairpin" in flux_text
    assert "苏晚在冷宫榻上惊醒" not in flux_text
    assert "苏晚 (穿越女主" not in flux_text


def test_project_prompt_to_flux_text_changes_composition_by_variant() -> None:
    prompt_markdown = """
    # shot-001

    ## Global Style

    vertical manhua palace style

    ## Shot Composition

    冷宫惊醒，月光照在脸上。
    """.strip()

    portrait_text = project_prompt_to_flux_text(prompt_markdown, variant_name="portrait")
    environment_text = project_prompt_to_flux_text(
        prompt_markdown,
        variant_name="environment",
    )

    assert "tight close-up" in portrait_text.lower()
    assert "wider medium shot" in environment_text.lower()
    assert portrait_text != environment_text


def test_build_flux_schnell_prompt_uses_checkpoint_and_vertical_size() -> None:
    prompt = build_flux_schnell_prompt(
        text="ancient palace manhua",
        negative_text="text, watermark, logo",
        checkpoint_name="flux1-schnell-fp8.safetensors",
        width=576,
        height=1024,
        seed=527002,
        steps=4,
        cfg=2.5,
        filename_prefix="ai_manga_demo_shot_001_flux_schnell",
    )

    assert prompt["30"]["inputs"]["ckpt_name"] == "flux1-schnell-fp8.safetensors"
    assert prompt["27"]["inputs"] == {"width": 576, "height": 1024, "batch_size": 1}
    assert prompt["31"]["inputs"]["seed"] == 527002
    assert prompt["31"]["inputs"]["steps"] == 4
    assert prompt["31"]["inputs"]["cfg"] == 2.5
    assert prompt["33"]["inputs"]["text"] == "text, watermark, logo"
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
    assert "tight close-up" in client.submitted_prompt["6"]["inputs"]["text"].lower()
    assert "watermark" in client.submitted_prompt["33"]["inputs"]["text"].lower()
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


def test_comfyui_client_wraps_service_unavailable_as_structural_error() -> None:
    client = ComfyUIClient(output_dir=Path("/tmp"))

    def raise_unavailable(path: str, payload: dict | None = None) -> dict:
        raise URLError("connection refused")

    client._json_request = raise_unavailable  # type: ignore[method-assign]

    try:
        client.queue_prompt({"30": {"class_type": "CheckpointLoaderSimple", "inputs": {}}})
    except ComfyUIStructuralError as exc:
        assert "unavailable" in str(exc).lower()
    else:
        raise AssertionError("Expected ComfyUIStructuralError")
