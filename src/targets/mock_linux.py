from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loguru import logger

from src.global_config import get_config


class MockLinuxTarget:
    """模拟 Linux 内核目标，提供补丁与源码文件访问。"""

    def __init__(self, kernel_root: Path | None = None):
        cfg = get_config()
        self.kernel_root = kernel_root or cfg.mock_kernel

    def get_patch(self, commit_id: str, commits: list[dict]) -> dict | None:
        for c in commits:
            if c["commit_id"] == commit_id:
                return c
        return None

    def load_commits(self) -> list[dict]:
        cfg = get_config()
        with open(cfg.commits_file, encoding="utf-8") as f:
            return json.load(f)

    def list_scan_files(self, modules: list[str] | None = None) -> list[Path]:
        modules = modules or get_config().pipeline.get("scan_modules", [])
        files: list[Path] = []
        for module in modules:
            module_path = self.kernel_root / module
            if module_path.exists():
                files.extend(module_path.rglob("*.c"))
        return sorted(files)

    def read_file(self, rel_path: str) -> str:
        path = self.kernel_root / rel_path
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    @staticmethod
    def get_object_name(file_name: str) -> str:
        return Path(file_name).stem + ".o"
