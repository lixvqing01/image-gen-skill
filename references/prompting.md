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
- Exclude device frames for UI unless explicitly requested.
- Prefer curated HSL-like palettes over flat primary colors.
- Use premium typography cues such as Inter, Roboto, or Outfit.
- Do not accept placeholder lorem ipsum when the request implies real content.
- Add smooth gradients, glass layers, or subtle motion cues only when they support the idea.
- Treat palette notes, font cues, project names, and style directions as internal control signals rather than on-canvas content.
- Unless the user explicitly asks for a style board, do not render color chips, palette swatches, font names, hex codes, layout notes, or labels like `Visual system` / `Font style`.

## Task-Type Defaults
### Normal
- Use interface-only compositions.
- Favor clean hierarchy, glass panels, dense but readable information blocks, and premium shadows.

### Architecture
- Favor layered blocks, clusters, connectors, and readable grouping.
- Ask for a cleanup pass if the diagram depends on exact small text.

### PPT
- Favor 16:9 layouts, title-safe spacing, and a repeatable visual system.
- Preserve a visual lane for title/body overlays when a slide will be rebuilt into PPT.

## Series Consistency
When the user needs multiple related slides or visuals:
1. Pick one `series_key`.
2. Keep the same `task_type`.
3. Add `--style-brief` only on the first call unless a deliberate style shift is required.
4. Reuse the same series manifest for all later calls.

## Editing with Input Images
- Pass at most 3 `--image-path` files.
- State what must remain unchanged.
- State exactly what should be added, removed, or transformed.
