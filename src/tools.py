from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from jinja2 import Template

from src.global_config import get_config


def load_template(name: str) -> str:
    cfg = get_config()
    path = cfg.prompt_template / name
    return path.read_text(encoding="utf-8")


def render_template(name: str, **kwargs: Any) -> str:
    template = Template(load_template(name))
    return template.render(**kwargs)


def load_knowledge(filename: str) -> str:
    cfg = get_config()
    path = cfg.prompt_template / "knowledge" / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def extract_function_from_patch(patch: str) -> str:
    match = re.search(r"@@.*?@@\n(.*)", patch, re.DOTALL)
    if match:
        return match.group(1).strip()
    return patch


def parse_commit_message(patch_data: dict[str, Any]) -> str:
    return patch_data.get("message", "")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
