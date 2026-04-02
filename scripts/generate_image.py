from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import sys
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

from _common import (
    DEFAULT_API_KEY,
    DEFAULT_API_FORMAT,
    DEFAULT_GEMINI_API_BASE,
    DEFAULT_MODEL,
    DEFAULT_OPENAI_API_URL,
    build_style,
    is_valid_aspect_ratio,
    load_or_create_series,
    normalize_task_type,
    now_iso,
    output_root,
    sanitize_series_key,
    sanitize_short_name,
    save_series,
    sidecars_dir,
    series_path,
    task_output_dir,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate or edit images with either an OpenAI-compatible or Gemini official image API.")
    parser.add_argument("--prompt", required=True, help="Main text prompt.")
    parser.add_argument("--image-name", required=True, help="lowercase_underscore name, max 3 words.")
    parser.add_argument(
        "--image-path",
        action="append",
        default=[],
        help="Optional existing image path. Repeat up to 3 times.",
    )
    parser.add_argument(
        "--task-type",
        choices=["normal", "architecture", "ppt"],
        help="Generation mode: ordinary image, architecture diagram, or PPT slide visual.",
    )
    parser.add_argument(
        "--mode",
        choices=["ui", "architecture", "slide", "asset"],
        help="Deprecated alias kept for compatibility. Prefer --task-type.",
    )
    parser.add_argument(
        "--aspect-ratio",
        default="16:9",
        help="Target aspect ratio such as 1:1, 4:3, 3:4, 16:9, 9:16, or 21:9.",
    )
    parser.add_argument(
        "--output-format",
        choices=["png", "jpg"],
        default="png",
        help="Final saved image format. Defaults to png.",
    )
    parser.add_argument("--series-key", help="Reuse a style series across multiple calls.")
    parser.add_argument("--slide-number", type=int, help="Optional explicit slide number for PPT task generation.")
    parser.add_argument(
        "--skip-series-manifest-update",
        action="store_true",
        help="Internal batch flag. Generate the image without appending to the shared series manifest.",
    )
    parser.add_argument("--style-brief", default="", help="Extra style guidance, mainly for the first series call.")
    parser.add_argument(
        "--output-subdir",
        help="Optional subfolder under codex_image_gen for grouping outputs. PPT series default to their own subfolder.",
    )
    parser.add_argument(
        "--api-format",
        choices=["openai", "gemini"],
        default=os.getenv("IMAGE_GEN_API_FORMAT", DEFAULT_API_FORMAT),
        help="API protocol. Use openai for OpenAI-compatible chat completions, or gemini for Google's official generateContent API.",
    )
    parser.add_argument(
        "--api-url",
        default=os.getenv("IMAGE_GEN_API_URL", ""),
        help="Full endpoint URL. If omitted, a default is chosen from --api-format.",
    )
    parser.add_argument("--model", default=os.getenv("IMAGE_GEN_MODEL", os.getenv("YUNWU_IMAGE_MODEL", DEFAULT_MODEL)))
    parser.add_argument(
        "--api-key",
        default=os.getenv(
            "IMAGE_GEN_API_KEY",
            os.getenv(
                "GEMINI_API_KEY",
                os.getenv(
                    "GOOGLE_API_KEY",
                    os.getenv(
                        "YUNWU_API_KEY",
                        os.getenv("OPENAI_API_KEY", DEFAULT_API_KEY),
                    ),
                ),
            ),
        ),
    )
    parser.add_argument("--output-root", help="Override the output folder. Defaults to ./codex_image_gen at project root.")
    parser.add_argument("--timeout", type=int, default=240, help="HTTP timeout in seconds.")
    parser.add_argument("--dry-run", action="store_true", help="Print the final prompt and exit without calling the API.")
    return parser.parse_args()


def image_data_url(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def image_inline_data(path: Path) -> dict:
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return {"inline_data": {"mime_type": mime, "data": payload}}


def resolve_api_url(api_format: str, api_url: str, model: str) -> str:
    if api_url.strip():
        return api_url.strip()
    if api_format == "gemini":
        return f"{DEFAULT_GEMINI_API_BASE}/models/{model}:generateContent"
    return DEFAULT_OPENAI_API_URL


def build_final_prompt(args: argparse.Namespace, style: dict) -> str:
    task_rules = {
        "normal": (
            "Generate a polished general-purpose image or UI-style visual. "
            "If the request is for a product interface, keep it interface-only and do not include device shells, "
            "browser chrome, or surrounding hardware unless explicitly requested."
        ),
        "architecture": (
            "Generate a clean project architecture or system map with grouped layers, readable labels, arrows, "
            "clear data or control flow, and structured information design."
        ),
        "ppt": (
            "Generate a presentation-ready slide visual with strong hierarchy, title-safe spacing, "
            "clear storytelling composition, and deck-quality polish."
        ),
    }
    edit_clause = (
        f"Use {len(args.image_path)} provided image(s) as edit/composite input. Preserve requested invariants."
        if args.image_path
        else "No input image is provided; generate from scratch."
    )
    series_clause = (
        f"Maintain consistency with series '{sanitize_series_key(args.series_key)}' using a shared visual language: "
        f"{style['visual_direction']} with a {style.get('color_story', 'premium restrained palette')} color story."
        if args.series_key
        else f"Use a {style['visual_direction']} visual language with a {style.get('color_story', 'premium restrained palette')} color story."
    )
    return (
        f"Goal: {args.prompt}\n"
        f"Task Type: {args.task_type}\n"
        f"Aspect Ratio: {args.aspect_ratio}\n"
        f"Usage: production-ready output\n"
        f"{series_clause}\n"
        f"Guidance: {task_rules[args.task_type]}\n"
        f"Edit Mode: {edit_clause}\n"
        "Ratio Guidance: Compose natively for the requested aspect ratio and avoid awkward cropping.\n"
        "Constraints: make the result visually striking; use a curated palette instead of generic flat primary colors; "
        "use modern sans-serif typography cues; avoid placeholders; use gradients, depth, and "
        "subtle motion cues when helpful; do not place the UI inside a laptop, phone, or tablet frame unless the prompt explicitly asks for it.\n"
        "Render only the intended final artwork. Do not render style-guide sidebars, mood-board notes, color chips, palette circles, font specimen cards, "
        "hex color codes, project codenames, layout annotations, labels such as 'visual system' or 'font style', or the names of fonts unless the user explicitly asks for a style board.\n"
        f"Style Notes: {style['prompt_suffix']}"
    )


def build_request_content(prompt: str, image_paths: list[Path]) -> str | list[dict]:
    if not image_paths:
        return prompt
    content = [{"type": "text", "text": prompt}]
    for path in image_paths:
        content.append({"type": "image_url", "image_url": {"url": image_data_url(path)}})
    return content


def build_gemini_parts(prompt: str, image_paths: list[Path]) -> list[dict]:
    parts = [{"text": prompt}]
    for path in image_paths:
        parts.append(image_inline_data(path))
    return parts


def extract_data_urls(value) -> list[str]:
    matches: list[str] = []

    def walk(node) -> None:
        if isinstance(node, str):
            matches.extend(
                re.findall(r"data:image/[a-zA-Z0-9.+-]+;base64,[A-Za-z0-9+/=\r\n]+", node)
            )
            return
        if isinstance(node, list):
            for item in node:
                walk(item)
            return
        if isinstance(node, dict):
            if "inlineData" in node and isinstance(node["inlineData"], dict):
                inline_data = node["inlineData"]
                mime_type = inline_data.get("mimeType")
                data = inline_data.get("data")
                if mime_type and data:
                    matches.append(f"data:{mime_type};base64,{data}")
            if "inline_data" in node and isinstance(node["inline_data"], dict):
                inline_data = node["inline_data"]
                mime_type = inline_data.get("mime_type")
                data = inline_data.get("data")
                if mime_type and data:
                    matches.append(f"data:{mime_type};base64,{data}")
            for child in node.values():
                walk(child)

    walk(value)
    seen = set()
    deduped = []
    for item in matches:
        if item not in seen:
            seen.add(item)
            deduped.append(item)
    return deduped


def next_ppt_slide_number(items: list[dict]) -> int:
    numbers = [
        int(item["slide_number"])
        for item in items
        if item.get("slide_number") is not None
    ]
    return (max(numbers) + 1) if numbers else 1


def convert_image_bytes(image_bytes: bytes, output_format: str, source_mime: str) -> bytes:
    if output_format == "png" and source_mime == "image/png":
        return image_bytes
    if output_format == "jpg" and source_mime in {"image/jpeg", "image/jpg"}:
        return image_bytes
    with Image.open(BytesIO(image_bytes)) as image:
        buffer = BytesIO()
        if output_format == "png":
            image.save(buffer, format="PNG")
        else:
            if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
                background = Image.new("RGB", image.size, (255, 255, 255))
                alpha = image.convert("RGBA")
                background.paste(alpha, mask=alpha.getchannel("A"))
                image = background
            else:
                image = image.convert("RGB")
            image.save(buffer, format="JPEG", quality=95)
        return buffer.getvalue()


def save_outputs(root: Path, image_name: str, data_urls: list[str], output_format: str) -> list[Path]:
    saved: list[Path] = []
    for index, data_url in enumerate(data_urls, start=1):
        header, payload = data_url.split(",", 1)
        source_mime = header.split(";")[0].split(":", 1)[1]
        original_bytes = base64.b64decode(payload)
        converted_bytes = convert_image_bytes(original_bytes, output_format, source_mime)
        extension = ".jpg" if output_format == "jpg" else ".png"
        filename = f"{image_name}{extension}" if len(data_urls) == 1 else f"{image_name}_{index:02d}{extension}"
        path = root / filename
        path.write_bytes(converted_bytes)
        saved.append(path)
    return saved


def send_openai_request(args: argparse.Namespace, final_prompt: str, image_paths: list[Path], resolved_api_url: str) -> dict:
    payload = {
        "model": args.model,
        "messages": [
            {
                "role": "user",
                "content": build_request_content(final_prompt, image_paths),
            }
        ],
    }
    response = requests.post(
        resolved_api_url,
        headers={
            "Authorization": f"Bearer {args.api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=args.timeout,
    )
    response.raise_for_status()
    return response.json()


def send_gemini_request(args: argparse.Namespace, final_prompt: str, image_paths: list[Path], resolved_api_url: str) -> dict:
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": build_gemini_parts(final_prompt, image_paths),
            }
        ],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
        },
    }
    response = requests.post(
        resolved_api_url,
        headers={
            "x-goog-api-key": args.api_key,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=args.timeout,
    )
    response.raise_for_status()
    return response.json()


def main() -> int:
    args = parse_args()
    if not args.task_type and not args.mode:
        print("Provide --task-type. Supported values: normal, architecture, ppt.", file=sys.stderr)
        return 2
    if args.task_type and args.mode:
        try:
            normalized_mode = normalize_task_type(args.mode)
        except ValueError:
            normalized_mode = None
        if normalized_mode is not None and normalized_mode != args.task_type:
            print("--task-type and --mode disagree. Use one or make them consistent.", file=sys.stderr)
            return 2
    try:
        args.task_type = normalize_task_type(args.task_type or args.mode)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    try:
        image_name = sanitize_short_name(args.image_name)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if len(args.image_path) > 3:
        print("Pass at most 3 --image-path values.", file=sys.stderr)
        return 2
    if args.slide_number is not None and args.task_type != "ppt":
        print("--slide-number is only valid when --task-type ppt.", file=sys.stderr)
        return 2
    if args.slide_number is not None and args.slide_number < 1:
        print("--slide-number must be a positive integer.", file=sys.stderr)
        return 2
    if not is_valid_aspect_ratio(args.aspect_ratio):
        print("--aspect-ratio must look like W:H with positive integers, for example 16:9.", file=sys.stderr)
        return 2

    image_paths = [Path(item).resolve() for item in args.image_path]
    missing = [str(path) for path in image_paths if not path.exists()]
    if missing:
        print(f"Missing input image(s): {', '.join(missing)}", file=sys.stderr)
        return 2

    series_record = None
    root = None
    if args.series_key:
        root = output_root(Path.cwd(), Path(args.output_root) if args.output_root else None)
        existing_series_path = series_path(root, args.series_key)
        if existing_series_path.exists():
            series_record = json.loads(existing_series_path.read_text(encoding="utf-8"))
            existing_task_type = series_record.get("style", {}).get("task_type")
            if existing_task_type and existing_task_type != args.task_type:
                print(
                    f"series_key '{sanitize_series_key(args.series_key)}' is already bound to task_type '{existing_task_type}'.",
                    file=sys.stderr,
                )
                return 2
            style = series_record["style"]
        else:
            style = build_style(args.task_type, args.style_brief)
    else:
        style = build_style(args.task_type, args.style_brief)

    final_prompt = build_final_prompt(args, style)

    if args.dry_run:
        print(f"API Format: {args.api_format}")
        print(f"API URL: {resolve_api_url(args.api_format, args.api_url, args.model)}")
        print(final_prompt)
        return 0

    if root is None:
        root = output_root(Path.cwd(), Path(args.output_root) if args.output_root else None)
    target_dir = task_output_dir(root, args.task_type, args.series_key, args.output_subdir)
    if args.series_key and series_record is None:
        series_record, _ = load_or_create_series(root, args.series_key, args.task_type, args.style_brief)
        style = series_record["style"]

    if (not args.api_key) or args.api_key == DEFAULT_API_KEY:
        print("Missing API key. Set IMAGE_GEN_API_KEY or pass --api-key.", file=sys.stderr)
        return 2
    resolved_api_url = resolve_api_url(args.api_format, args.api_url, args.model)
    if args.api_format == "gemini":
        result = send_gemini_request(args, final_prompt, image_paths, resolved_api_url)
    else:
        result = send_openai_request(args, final_prompt, image_paths, resolved_api_url)

    data_urls = extract_data_urls(result)
    if not data_urls:
        sidecar_root = sidecars_dir(target_dir)
        raw_path = sidecar_root / f"{image_name}_raw_response.json"
        raw_path.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="utf-8")
        print(f"No image payload found. Raw response saved to {raw_path}", file=sys.stderr)
        return 1

    final_image_name = image_name
    slide_number = None
    if args.task_type == "ppt":
        slide_number = args.slide_number
        if slide_number is None and series_record is not None:
            slide_number = next_ppt_slide_number(series_record["items"])
    if slide_number is not None:
        final_image_name = f"{slide_number:02d}_{image_name}"

    saved_paths = save_outputs(target_dir, final_image_name, data_urls, args.output_format)
    metadata = {
        "created_at": now_iso(),
        "task_type": args.task_type,
        "aspect_ratio": args.aspect_ratio,
        "output_format": args.output_format,
        "image_name": final_image_name,
        "requested_image_name": image_name,
        "series_key": sanitize_series_key(args.series_key) if args.series_key else None,
        "slide_number": slide_number,
        "prompt": final_prompt,
        "input_images": [str(path) for path in image_paths],
        "outputs": [str(path) for path in saved_paths],
        "output_subdir": target_dir.name if target_dir != root else None,
        "model": args.model,
        "api_format": args.api_format,
        "api_url": resolved_api_url,
        "response_id": result.get("id") or result.get("responseId"),
    }

    sidecar_root = sidecars_dir(target_dir)
    (sidecar_root / f"{final_image_name}.prompt.txt").write_text(final_prompt, encoding="utf-8")
    (sidecar_root / f"{final_image_name}.json").write_text(
        json.dumps(metadata, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )

    if series_record is not None and not args.skip_series_manifest_update:
        series_record["items"].append(
            {
                "image_name": final_image_name,
                "requested_image_name": image_name,
                "created_at": metadata["created_at"],
                "task_type": args.task_type,
                "aspect_ratio": args.aspect_ratio,
                "output_format": args.output_format,
                "slide_number": slide_number,
                "prompt": args.prompt,
                "saved_paths": metadata["outputs"],
            }
        )
        save_series(root, series_record)

    for path in saved_paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
