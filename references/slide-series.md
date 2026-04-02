# Slide Series

Use a shared `series_key` to keep a whole deck in one visual language.

## Recommended Flow
1. Pick one `series_key`, for example `investor_deck`.
2. If there are many slides, use the global batch script `generate_slide_series.py`.
3. Set a shared `aspect_ratio`, usually `16:9`.
4. Set `output_format` to `png` unless you explicitly want `jpg`.
5. Otherwise generate each slide with `--task-type ppt`.
6. Keep `--image-name` descriptive and short.
7. Let the script auto-number the final filename.
8. Expect output files under a subfolder such as `codex_image_gen/investor_deck/`.

## Example
```powershell
python scripts/generate_image.py `
  --task-type ppt `
  --series-key investor_deck `
  --aspect-ratio 16:9 `
  --output-format png `
  --prompt "Create a cover slide for an AI platform launch with bold gradient lighting." `
  --image-name cover

python scripts/generate_image.py `
  --task-type ppt `
  --series-key investor_deck `
  --aspect-ratio 16:9 `
  --output-format png `
  --prompt "Create a system architecture slide with layered services and data flow." `
  --image-name architecture
```

This produces files such as:
- `01_cover.jpg`
- `02_architecture.jpg`

## Batch JSON
When the slide list is already known, prefer a single JSON file and one global command:

```json
{
  "series_key": "investor_deck",
  "aspect_ratio": "16:9",
  "output_format": "png",
  "style_brief": "dark glass, restrained teal accent, editorial deck",
  "output_subdir": "investor_deck",
  "slides": [
    {
      "image_name": "cover",
      "prompt": "Create a cover slide for an AI platform launch with bold gradient lighting."
    },
    {
      "image_name": "architecture",
      "prompt": "Create a system architecture slide with layered services and data flow."
    }
  ]
}
```

```powershell
python <skill_dir>\scripts\generate_slide_series.py `
  --slides-file C:\path\to\slides.json
```

## Manual Number Override
Use `--slide-number` only when you must pin a specific order:

```powershell
python scripts/generate_image.py `
  --task-type ppt `
  --series-key investor_deck `
  --aspect-ratio 16:9 `
  --output-format jpg `
  --slide-number 7 `
  --prompt "Create a roadmap slide with milestone ribbons." `
  --image-name roadmap
```
