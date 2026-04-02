# image-gen-skill

Image generation skill for Codex-style agents.

It supports:
- `normal` image generation
- `architecture` diagrams
- `ppt` slide-image generation
- parallel PPT batch generation from a JSON manifest
- output format selection: `png` by default, `jpg` supported
- `openai`-compatible endpoints
- official Google Gemini `generateContent` API

## Structure
- `SKILL.md`: skill instructions and trigger behavior
- `scripts/generate_image.py`: single-image entrypoint
- `scripts/generate_slide_series.py`: parallel PPT batch entrypoint
- `references/`: prompting and slide-series notes

## Authentication
Supported environment variables:
- `IMAGE_GEN_API_KEY`
- `IMAGE_GEN_API_URL`
- `IMAGE_GEN_MODEL`
- `GEMINI_API_KEY`
- `GOOGLE_API_KEY`
- `YUNWU_API_KEY`
- `OPENAI_API_KEY`

Or replace the placeholder `YOUR_IMAGE_API_KEY` in [`scripts/_common.py`](./scripts/_common.py).

## API Formats
The script supports two protocol modes:

- `openai`
  Use any OpenAI-compatible chat completions endpoint.
  Example default: `https://yunwu.ai/v1/chat/completions`

- `gemini`
  Use the official Google Gemini `generateContent` API.
  If `--api-url` is omitted, the script builds:
  `https://generativelanguage.googleapis.com/v1beta/models/<model>:generateContent`

Default model:
- `gemini-3.1-flash-image-preview`

## Single Image
```powershell
python .\scripts\generate_image.py `
  --api-format openai `
  --task-type normal `
  --aspect-ratio 16:9 `
  --output-format png `
  --prompt "Create a premium product hero visual with dark glass panels and teal accent lighting." `
  --image-name hero_visual
```

## Official Gemini Example
```powershell
python .\scripts\generate_image.py `
  --api-format gemini `
  --model gemini-2.5-flash-image-preview `
  --task-type normal `
  --aspect-ratio 16:9 `
  --output-format png `
  --prompt "Create a premium product hero visual with dark glass panels and teal accent lighting." `
  --image-name hero_visual
```

## Architecture Diagram
```powershell
python .\scripts\generate_image.py `
  --api-format openai `
  --task-type architecture `
  --aspect-ratio 16:9 `
  --output-format png `
  --prompt "Create a clean cloud-native system architecture diagram with ingestion, orchestration, storage, analytics, and observability layers." `
  --image-name system_architecture
```

## PPT Slide
```powershell
python .\scripts\generate_image.py `
  --api-format openai `
  --task-type ppt `
  --aspect-ratio 16:9 `
  --output-format png `
  --prompt "Create a premium title slide for an AI platform launch with clear title space." `
  --image-name cover `
  --series-key investor_deck
```

## Parallel PPT Batch
Example manifest:

```json
{
  "series_key": "investor_deck",
  "api_format": "gemini",
  "model": "gemini-2.5-flash-image-preview",
  "aspect_ratio": "16:9",
  "output_format": "png",
  "style_brief": "dark editorial deck with teal accent",
  "output_subdir": "investor_deck",
  "slides": [
    {
      "image_name": "cover",
      "prompt": "Create a premium title slide for an AI platform launch with clear title space."
    },
    {
      "image_name": "roadmap",
      "prompt": "Create a roadmap slide with milestone ribbons and presentation styling."
    }
  ]
}
```

Run:

```powershell
python .\scripts\generate_slide_series.py --slides-file .\slides.json --max-workers 3
```

## Output
Generated files are written under:
- `codex_image_gen/`

Typical layout:
- `codex_image_gen/<subdir>/*.png|*.jpg`
- `codex_image_gen/<subdir>/metadata/*`
- `codex_image_gen/series/<series_key>.json`

## Notes
- UI-style outputs are intended to avoid device frames unless explicitly requested.
- The prompting logic tries to avoid leaking style-guide text like palette names, font labels, and internal project codenames into the final image.
