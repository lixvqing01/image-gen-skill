from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_OPENAI_API_URL = "https://yunwu.ai/v1/chat/completions"
DEFAULT_GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_API_FORMAT = "openai"
DEFAULT_MODEL = "gemini-3.1-flash-image-preview"
DEFAULT_API_KEY = "YOUR_IMAGE_API_KEY"
OUTPUT_DIR_NAME = "codex_image_gen"
TASK_TYPE_ALIAS = {
    "ui": "normal",
    "asset": "normal",
    "slide": "ppt",
    "architecture": "architecture",
}

STYLE_LIBRARY = {
    "normal": {
        "visual_direction": "luminous glass product design",
        "palette": ["#08111F", "#12324B", "#1A7F8E", "#63E6BE", "#F7FAFF"],
        "font_family": "Outfit",
        "color_story": "deep navy, ink blue, luminous teal, soft mint, and clean white",
        "prompt_suffix": (
            "Create a premium production-ready image with a curated high-contrast palette, "
            "refined gradients, polished depth, modern sans-serif typography cues "
            "when text is needed, and no placeholder content."
        ),
    },
    "architecture": {
        "visual_direction": "cinematic systems diagram",
        "palette": ["#07111E", "#0F3B53", "#21B8B2", "#FFC857", "#F8FBFF"],
        "font_family": "Inter",
        "color_story": "midnight blue, ocean teal, signal cyan, restrained gold, and crisp white",
        "prompt_suffix": (
            "Create a polished architecture diagram with grouped layers, directional connectors, "
            "balanced spacing, crisp iconography, readable labels, subtle depth, and no device frame."
        ),
    },
    "ppt": {
        "visual_direction": "editorial deck visual system",
        "palette": ["#08111F", "#13233B", "#4EA8DE", "#63E6BE", "#F7FAFF"],
        "font_family": "Outfit",
        "color_story": "dark navy, slate blue, electric azure, bright teal, and soft white",
        "prompt_suffix": (
            "Create a presentation slide visual with a premium deck aesthetic, "
            "clear title-safe spacing, cohesive gradients, modern sans-serif typography cues, "
            "and strong visual hierarchy."
        ),
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sanitize_short_name(value: str) -> str:
    name = value.strip().lower()
    if not re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+){0,2}", name):
        raise ValueError(
            "image_name must be lowercase, underscore-separated, and contain at most 3 words."
        )
    return name


def sanitize_series_key(value: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    if not key:
        raise ValueError("series_key must contain letters or digits.")
    return key


def normalize_task_type(value: str) -> str:
    normalized = value.strip().lower()
    mapped = TASK_TYPE_ALIAS.get(normalized, normalized)
    if mapped not in STYLE_LIBRARY:
        raise ValueError(f"Unsupported task_type: {value}")
    return mapped


def normalize_style_brief_for_prompt(value: str) -> str:
    brief = value.strip()
    if not brief:
        return brief
    if re.fullmatch(r"[A-Za-z0-9_-]+", brief):
        return "follow the established project visual identity without showing its internal codename"
    return brief


def is_valid_aspect_ratio(value: str) -> bool:
    match = re.fullmatch(r"\s*(\d{1,3})\s*:\s*(\d{1,3})\s*", value)
    if not match:
        return False
    left = int(match.group(1))
    right = int(match.group(2))
    return left > 0 and right > 0


def detect_project_root(start: Path) -> Path:
    start = start.resolve()
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    return start


def output_root(start: Path | None = None, explicit: Path | None = None) -> Path:
    if explicit is not None:
        root = explicit.resolve()
    else:
        root = detect_project_root(start or Path.cwd()) / OUTPUT_DIR_NAME
    root.mkdir(parents=True, exist_ok=True)
    return root


def series_dir(root: Path) -> Path:
    path = root / "series"
    path.mkdir(parents=True, exist_ok=True)
    return path


def sidecars_dir(root: Path) -> Path:
    path = root / "metadata"
    path.mkdir(parents=True, exist_ok=True)
    return path


def series_path(root: Path, series_key: str) -> Path:
    return series_dir(root) / f"{sanitize_series_key(series_key)}.json"


def task_output_dir(root: Path, task_type: str, series_key: str | None = None, output_subdir: str | None = None) -> Path:
    if output_subdir:
        target = root / sanitize_series_key(output_subdir)
    elif task_type == "ppt" and series_key:
        target = root / sanitize_series_key(series_key)
    else:
        target = root
    target.mkdir(parents=True, exist_ok=True)
    return target


def build_style(task_type: str, style_brief: str = "") -> dict:
    normalized_task_type = normalize_task_type(task_type)
    style = deepcopy(STYLE_LIBRARY[normalized_task_type])
    style["task_type"] = normalized_task_type
    style["style_brief"] = style_brief.strip()
    prompt_safe_brief = normalize_style_brief_for_prompt(style_brief)
    if prompt_safe_brief:
        style["prompt_suffix"] = f'{style["prompt_suffix"]} Extra style direction: {prompt_safe_brief}.'
    return style


def load_or_create_series(root: Path, series_key: str, task_type: str, style_brief: str = "") -> tuple[dict, bool]:
    path = series_path(root, series_key)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8")), False

    record = {
        "series_key": sanitize_series_key(series_key),
        "created_at": now_iso(),
        "style": build_style(task_type, style_brief),
        "items": [],
    }
    path.write_text(json.dumps(record, ensure_ascii=True, indent=2), encoding="utf-8")
    return record, True


def save_series(root: Path, record: dict) -> Path:
    path = series_path(root, record["series_key"])
    path.write_text(json.dumps(record, ensure_ascii=True, indent=2), encoding="utf-8")
    return path
