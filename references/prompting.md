# Prompting Guide

## Shared Prompt Frame
Use this structure when turning a user request into the final prompt:

```text
Goal: <what to generate or edit>
Task Type: <normal | architecture | ppt>
Aspect Ratio: <1:1 | 4:3 | 16:9 | 9:16 | ...>
Audience/Use: <landing page, investor deck, internal review, product site, etc.>
Visual Direction: <style language>
Composition: <layout or framing>
Content Requirements: <must-show features or labels>
Constraints: <keep/remove/avoid>
```

## Hard Rules
- Aim for immediate visual impact with deliberate hierarchy and premium contrast.
- Exclude device frames for UI unless explicitly requested.
- Prefer curated HSL-like palettes over flat primary colors.
- Use premium typography cues; references like Inter, Roboto, or Outfit are guidance, not text to render on canvas.
- Do not accept placeholder lorem ipsum when the request implies real content.
- Add smooth gradients, glass layers, or subtle motion cues only when they support the idea.
- Treat palette notes, font cues, project names, and style directions as internal control signals rather than on-canvas content.
- Unless the user explicitly asks for a style board, do not render color chips, palette swatches, font names, hex codes, layout notes, or labels like `Visual system` / `Font style`.
- Default to a publication-grade aesthetic: clean neutral bases, high-contrast labels, accessible accent colors, and restrained decoration.
- Avoid rainbow scales, avoid red-green dependent coding, and avoid colored text when keylines plus black or white labels will read more clearly.

## Task-Type Defaults
### Normal
- Use interface-only compositions.
- Favor tailored composition, dense but readable information blocks, premium shadows, and glass panels only when they improve the concept.

### Architecture
- Favor layered blocks, clusters, connectors, readable grouping, and short labels that survive image-model drift.
- Ask for a cleanup pass if the diagram depends on exact small text.

### PPT
- Favor 16:9 layouts, title-safe spacing, a single focal narrative, and a repeatable visual system.
- Preserve a visual lane for title/body overlays when a slide will be rebuilt into PPT.

## Series Consistency
When the user needs multiple related slides or visuals:
1. Pick one `series_key`.
2. Keep the same `task_type`.
3. Add `--style-brief` only on the first call unless a deliberate style shift is required.
4. Reuse the same series manifest for all later calls.

## Writing `style_brief`
- Use `style_brief` to steer taste, not content.
- Keep it compact and noun-heavy; avoid full-sentence prose.
- Include up to four ingredients:
  `base tone`, `accent family`, `surface treatment`, `layout mood`
- Prefer one coherent family over mixed signals.

Reference briefs:
- `cool white base, graphite labels, accessible blue-orange-green-magenta accents, publication-grade clarity`
- `warm paper background, charcoal hierarchy, muted teal and ochre accents, restrained report layout`
- `deep academic navy, aurora blue-violet gradient, crisp white typography, premium research keynote mood`
- `off-white canvas, black keylines, single cyan accent, monochrome scientific figure`
- `softened complementary palette, single focal process, sparse labels, clean biological storytelling`
- `deep charcoal base, electric cyan-to-violet gradients, luminous glass panels, cinematic contrast`
- `midnight navy backdrop, aurora gradients, soft bloom lighting, refined editorial spacing`
- `warm ivory background, graphite text, muted bronze accents, flat premium surfaces`
- `matte black canvas, stone gray structure, restrained emerald accents, minimal premium UI`
- `cool white base, graphite hierarchy, surgical cyan highlights, restrained depth`
- `cream background, espresso typography, bronze accents, luxury magazine layout`

Use gradient-led briefs when the user wants spectacle, motion, launch visuals, futuristic product energy, or deck covers.
Use minimal solid-color briefs when the user wants trust, restraint, enterprise clarity, editorial calm, or information-first layouts.
Use journal/report briefs when the user wants publication credibility, scientific clarity, reviewer-friendly figures, or academic presentation visuals.

## Editing with Input Images
- Pass at most 3 `--image-path` files.
- State what must remain unchanged.
- State exactly what should be added, removed, or transformed.
