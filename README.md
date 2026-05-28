# ai-manga-studio

Local development workspace for AI manga production.

## Layout

- `apps/web`: Next.js frontend
- `apps/api`: FastAPI backend
- `packages/shared`: shared utilities and types
- `storage/`: local projects, assets, renders, and models
- `docs/`: project notes and specs
- `scripts/`: automation scripts

## Local ComfyUI Candidate

With ComfyUI running at `http://127.0.0.1:8188`, generate and import local image candidates.

Single-shot candidate generation:

```bash
uv run python scripts/comfy_generate.py --project demo-001 --shot shot-001 --variants 2
```

Project-wide candidate generation:

```bash
uv run python scripts/comfy_generate.py --project demo-001 --variants 2 --replace-source comfyui
```

Generated binaries stay local under `storage/projects/<project>/candidates/`; review a candidate before promoting it to `stills/`.
