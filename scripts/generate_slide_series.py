from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from _common import DEFAULT_MODEL, load_or_create_series, now_iso, output_root, save_series, task_output_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a whole slide series from one JSON manifest.")
    parser.add_argument("--slides-file", required=True, help="Path to a JSON manifest describing the slide series.")
    parser.add_argument("--output-root", help="Optional override for codex_image_gen root.")
    parser.add_argument("--api-key", help="Optional API key override passed through to generate_image.py.")
    parser.add_argument("--max-workers", type=int, default=4, help="Parallel worker count for PPT slide generation.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned commands without calling the image API.")
    return parser.parse_args()


def build_command(
    script_path: Path,
    series_key: str,
    api_format: str,
    api_url: str,
    model: str,
    api_key: str | None,
    style_brief: str,
    aspect_ratio: str,
    output_format: str,
    output_root: str | None,
    output_subdir: str,
    slide_number: int,
    slide: dict,
    dry_run: bool,
) -> list[str]:
    command = [
        sys.executable,
        str(script_path),
        "--task-type",
        "ppt",
        "--api-format",
        slide.get("api_format", api_format),
        "--series-key",
        series_key,
        "--aspect-ratio",
        slide.get("aspect_ratio", aspect_ratio),
        "--output-format",
        slide.get("output_format", output_format),
        "--model",
        slide.get("model", model),
        "--prompt",
        slide["prompt"],
        "--image-name",
        slide["image_name"],
        "--slide-number",
        str(slide.get("slide_number", slide_number)),
        "--output-subdir",
        output_subdir,
        "--skip-series-manifest-update",
    ]
    if style_brief:
        command.extend(["--style-brief", slide.get("style_brief", style_brief)])
    elif slide.get("style_brief"):
        command.extend(["--style-brief", slide["style_brief"]])
    resolved_api_url = slide.get("api_url", api_url)
    if resolved_api_url:
        command.extend(["--api-url", resolved_api_url])
    resolved_api_key = slide.get("api_key", api_key)
    if resolved_api_key:
        command.extend(["--api-key", resolved_api_key])
    if output_root:
        command.extend(["--output-root", output_root])
    if dry_run:
        command.append("--dry-run")
    for image_path in slide.get("image_paths", []):
        command.extend(["--image-path", str(image_path)])
    return command


def run_one(command: list[str]) -> None:
    subprocess.run(command, check=True)


def main() -> int:
    args = parse_args()
    if args.max_workers < 1:
        print("--max-workers must be at least 1.", file=sys.stderr)
        return 2
    slides_path = Path(args.slides_file).resolve()
    payload = json.loads(slides_path.read_text(encoding="utf-8"))

    series_key = payload["series_key"]
    api_format = payload.get("api_format", "openai")
    api_url = payload.get("api_url", "")
    model = payload.get("model", DEFAULT_MODEL)
    style_brief = payload.get("style_brief", "")
    aspect_ratio = payload.get("aspect_ratio", "16:9")
    output_format = payload.get("output_format", "png")
    slides = payload["slides"]
    if not slides:
        print("slides-file must include at least one slide.", file=sys.stderr)
        return 2
    script_path = Path(__file__).resolve().with_name("generate_image.py")
    output_subdir = payload.get("output_subdir", series_key)

    commands = [
        build_command(
            script_path=script_path,
            series_key=series_key,
            api_format=api_format,
            api_url=api_url,
            model=model,
            api_key=args.api_key,
            style_brief=style_brief,
            aspect_ratio=aspect_ratio,
            output_format=output_format,
            output_root=args.output_root,
            output_subdir=output_subdir,
            slide_number=index,
            slide=slide,
            dry_run=args.dry_run,
        )
        for index, slide in enumerate(slides, start=1)
    ]

    if args.dry_run:
        for command in commands:
            print(subprocess.list2cmdline(command))
        return 0

    root = output_root(Path.cwd(), Path(args.output_root) if args.output_root else None)
    target_dir = task_output_dir(root, "ppt", series_key, output_subdir)
    series_record, _ = load_or_create_series(root, series_key, "ppt", style_brief)

    max_workers = max(1, min(args.max_workers, len(commands)))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_one, command) for command in commands]
        for future in as_completed(futures):
            future.result()

    items = []
    for index, slide in enumerate(slides, start=1):
        slide_number = slide.get("slide_number", index)
        image_name = f"{slide_number:02d}_{slide['image_name']}"
        matches = sorted(target_dir.glob(f"{image_name}*"))
        saved_paths = [str(path.resolve()) for path in matches if path.is_file() and path.parent == target_dir]
        items.append(
            {
                "image_name": image_name,
                "requested_image_name": slide["image_name"],
                "created_at": now_iso(),
                "task_type": "ppt",
                "aspect_ratio": slide.get("aspect_ratio", aspect_ratio),
                "output_format": slide.get("output_format", output_format),
                "slide_number": slide_number,
                "prompt": slide["prompt"],
                "saved_paths": saved_paths,
            }
        )

    series_record["items"] = items
    series_record["output_subdir"] = target_dir.name
    save_series(root, series_record)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
