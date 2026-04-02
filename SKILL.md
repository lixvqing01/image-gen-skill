---
name: generate-image
description: "Generate or edit high-fidelity raster images by calling either an OpenAI-compatible image endpoint or the official Gemini generateContent API, with explicit task-type and aspect-ratio inputs. Use when Codex needs to: (1) create ordinary product or visual assets, (2) draw project architecture or system diagrams, or (3) generate multiple PPT slide images in one visual language. Supports prompt-driven generation plus editing/compositing from up to 3 input images, and parallel PPT batch generation into a dedicated output subfolder."
---

# Generate Image

Use the bundled scripts instead of writing one-off API clients.

## Non-Negotiable Execution Rules
- Always use the bundled scripts inside this skill folder.
- Do not search the current project for similar image-generation or slide-generation scripts before using this skill.
- Do not inspect local project `scripts/`, `tools/`, or `utils/` folders unless the user explicitly asks to modify or compare the project's own implementation.
- You may inspect project asset folders such as `assets/`, `figures/`, `images/`, `exports/`, `results/`, `docs/`, or `slides/` when looking for reusable charts, maps, screenshots, diagrams, or report figures to feed into this skill.
- Resolve script paths relative to this `SKILL.md` file and use `scripts/generate_image.py` or `scripts/generate_slide_series.py`.
- For one image, call the bundled skill script directly.
- For a deck or multi-slide batch, prefer the bundled `generate_slide_series.py` script instead of repeated manual orchestration.

## Bundled Script Root
- `scripts/generate_image.py`
- `scripts/generate_slide_series.py`

## Core Workflow
1. Pick a task type:
   - `normal` for ordinary image generation, UI visuals, product graphics, and generic design assets.
   - `architecture` for project structure, system diagrams, data flow, and platform maps.
   - `ppt` for presentation slide images.
2. Pick an aspect ratio such as `1:1`, `4:3`, `16:9`, or `9:16`.
3. Pick an output format: `png` by default, or `jpg` when smaller files are preferred.
4. If editing or compositing, provide up to 3 `--image-path` inputs.
5. Call `scripts/generate_image.py` with:
   - `--prompt`
   - `--task-type`
   - `--aspect-ratio`
   - `--output-format`
   - `--image-name`
   - optional repeated `--image-path` up to 3 files
6. Reuse `--series-key` when generating multiple related images so the script keeps palette, typography, and layout language consistent across calls.
7. For PPT slide series, the script auto-prefixes the saved image names with `01_`, `02_`, `03_` and so on. Use `--slide-number` only when you need to force a specific sequence number.
8. When the user already knows the slide list, skip repeated single-slide calls and use `generate_slide_series.py`.
9. For multi-slide PPT work, outputs go into a dedicated subfolder under `codex_image_gen/`, typically named after the series key.
10. When the user cares about a specific visual taste, add a concise `--style-brief` instead of overloading the main prompt with styling clauses.
11. For PPT and architecture work, actively look for reusable project visuals such as exported maps, charts, legends, screenshots, PDFs, and figure crops, then pass them as `--image-path` inputs when they should appear in the final composition.

## Required Parameters
- `--prompt`: natural-language generation or edit request.
- `--task-type`: `normal`, `architecture`, or `ppt`.
- `--aspect-ratio`: the intended output ratio.
- `--output-format`: `png` by default, or `jpg`.
- `--image-name`: lowercase, underscore-separated, at most 3 words. Example: `login_page_mockup`.
- `--image-path`: optional existing images for edit/composite workflows. Pass at most 3.

## Output Rules
- Save final artifacts under a `codex_image_gen/` folder at the detected project root.
- If no repo root is found, fall back to the current working directory.
- Save image outputs plus prompt/metadata sidecars so later iterations remain traceable.
- Save series manifests under `codex_image_gen/series/`.
- For PPT series, save generated slide images into a child folder such as `codex_image_gen/investor_deck/`.

## Authentication and Runtime
- `--api-format openai`: use any OpenAI-compatible chat completions endpoint. If `--api-url` is omitted, the default example endpoint is `https://yunwu.ai/v1/chat/completions`.
- `--api-format gemini`: use the official Gemini `generateContent` API. If `--api-url` is omitted, the script builds the official Google endpoint from `--model`.
- Default model: `gemini-3.1-flash-image-preview`
- Replace the placeholder `YOUR_IMAGE_API_KEY` in `scripts/_common.py`, or set `IMAGE_GEN_API_KEY`, or pass `--api-key ...` explicitly.
- `IMAGE_GEN_API_URL` and `IMAGE_GEN_MODEL` are the preferred generic env vars for endpoint and model overrides.
- `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `YUNWU_API_KEY`, and `OPENAI_API_KEY` are also accepted as fallback env vars for compatibility.

## Design Rules
- Aim for immediate visual impact. Favor bold but controlled color systems, premium contrast, and clear hierarchy.
- Avoid generic pure red, pure blue, or pure green palettes when a richer palette will work better.
- Prefer modern typography cues. References like Inter, Roboto, or Outfit are guidance for the aesthetic, not text to render on canvas.
- Avoid placeholder content. If a mockup or slide needs imagery, generate it.
- Use gradients, depth, glass-like layering, and subtle motion cues when they improve the result.
- Treat palette notes, typography notes, and style directions as internal control signals rather than visible slide content.
- Do not include laptop, phone, tablet, or browser chrome around UI screens unless the user explicitly asks for a device/mockup frame.
- Default to a top-journal / academic-report baseline: clean neutral backgrounds, accessible accent colors, high text contrast, sparse color usage, and restrained decoration.
- Avoid rainbow scales, avoid relying on red-green pairings to encode meaning, and avoid colored text when black/white labels with keylines will read better.

## Task-Type Guidance
### Normal
- Use for ordinary image generation, UI concepts, posters, marketing visuals, and product graphics.
- If the request is for a UI, keep the output interface-only and avoid device frames unless explicitly requested.
- Adapt composition to the specified aspect ratio instead of assuming a fixed canvas.

### Architecture
- Use for project architecture, platform diagrams, service topology, component flows, and process maps.
- Ask for a follow-up edit if exact text labels must be perfect; image models can drift on small text.
- Prefer grouped subsystems, directional arrows, and clearly separated layers.
- Prefer white or softly tinted report boards, thin borders, masked map or chart insets, and explicit framed modules.
- If the project already has maps, rasters, legends, plots, or workflow sketches, reuse them as source assets instead of redrawing them.

### PPT
- Default to `16:9` unless the user specifies another ratio.
- Reuse a `--series-key` for multi-slide work.
- For many slides, use `generate_slide_series.py` so slide generation runs in parallel.
- Save slide images into a series-specific child folder and keep numbering explicit.
- Favor board-like slide layouts with bordered cards, clipped panels, side callout stacks, and consistent gutters.
- If project figures already exist, compose them into the slide as masked content blocks before inventing new imagery.

## Style-Brief Guidance
- Use `--style-brief` when the user wants a specific taste, art direction, or brand mood.
- Keep it short and concrete: 5 to 12 words is usually enough.
- Focus on palette mood, surface treatment, contrast level, composition feel, and typography character.
- Treat it as an internal control phrase. Do not ask the model to render the style brief itself.
- Prefer one dominant direction instead of mixing many incompatible aesthetics.

## Style-Brief Reference Patterns
- Nature-style accessible figure:
  `cool white base, graphite labels, accessible blue-orange-green-magenta accents, publication-grade clarity`
- Academic report minimal:
  `warm paper background, charcoal hierarchy, muted teal and ochre accents, restrained report layout`
- Board-style research delivery:
  `powder blue background, thin teal keylines, rounded white cards, masked figure panels, report board layout`
- Framed scientific dashboard:
  `soft blue-gray base, graphite titles, framed heatmap panels, side callout stack, clean delivery slide`
- Scientific keynote cover:
  `deep academic navy, aurora blue-violet gradient, crisp white typography, premium research keynote mood`
- Methods-figure monochrome:
  `off-white canvas, black keylines, single cyan accent, monochrome scientific figure`
- Cell-style graphical abstract:
  `softened complementary palette, single focal process, sparse labels, clean biological storytelling`
- Premium gradient tech:
  `deep charcoal base, electric cyan-to-violet gradients, luminous glass panels, cinematic contrast`
- Premium gradient editorial:
  `midnight navy backdrop, aurora gradients, soft bloom lighting, refined editorial spacing`
- Minimal solid-color light:
  `warm ivory background, graphite text, muted bronze accents, flat premium surfaces`
- Minimal solid-color dark:
  `matte black canvas, stone gray structure, restrained emerald accents, minimal premium UI`
- Quiet enterprise architecture:
  `cool white base, graphite hierarchy, surgical cyan highlights, restrained depth`
- Luxury print-inspired dashboard:
  `cream background, espresso typography, bronze accents, luxury magazine layout`

## Style-Brief Writing Formula
- Use this pattern when inventing a new one:
  `<base tone>, <accent family>, <surface treatment>, <layout or mood>`
- Good:
  `soft sand background, slate typography, muted coral accents, calm editorial layout`
- Good:
  `graphite base, icy blue highlights, subtle glass depth, focused enterprise composition`
- Avoid:
  long paragraph-style briefs, contradictory directions, or raw font names / hex codes unless the user explicitly wants a style board

## Journal-Derived Default Baseline
- Use a Nature / Cell / Elsevier-inspired baseline unless the user clearly wants a different visual language.
- Start from neutral white, ivory, stone, graphite, or academic navy foundations.
- Add only a few softened accent colors, ideally from an accessible figure palette.
- Let layout, grouping, keylines, and contrast carry the information before color does.
- Use stronger gradients and glow only for covers, keynote openers, or hero visuals; keep methods figures and report diagrams quieter.

## Commands
```powershell
python <skill_dir>\scripts\generate_image.py `
  --api-format openai `
  --task-type normal `
  --aspect-ratio 16:9 `
  --output-format png `
  --prompt "Design a cinematic SaaS analytics dashboard for carbon trading." `
  --image-name analytics_dashboard
```

```powershell
python <skill_dir>\scripts\generate_image.py `
  --api-format openai `
  --task-type architecture `
  --aspect-ratio 16:9 `
  --output-format png `
  --prompt "Draw a cloud-native RAG system with ingestion, vector store, orchestration, and observability." `
  --image-name rag_architecture `
  --series-key investor_deck
```

```powershell
python <skill_dir>\scripts\generate_image.py `
  --api-format gemini `
  --model gemini-2.5-flash-image-preview `
  --task-type ppt `
  --aspect-ratio 16:9 `
  --output-format png `
  --prompt "Create an executive-summary slide for an AI platform launch with room for a title and three bullets." `
  --image-name exec_summary `
  --series-key investor_deck
```

```powershell
python <skill_dir>\scripts\generate_slide_series.py `
  --slides-file C:\path\to\slides.json
```

## References
- Read `references/prompting.md` for prompt shaping and mode-specific guidance.
- Read `references/slide-series.md` when you need explicit numbering and multi-slide workflow guidance.

## Scripts
- `scripts/generate_image.py`: generate or edit images and maintain style consistency across a series.
- `scripts/generate_slide_series.py`: generate a whole PPT slide series from one JSON manifest, in parallel, into a dedicated output subfolder.
- `scripts/_common.py`: shared path, naming, and series helpers.
