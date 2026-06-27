from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class AppConfig:
    raw: dict[str, Any] = field(default_factory=dict)
    root: Path = field(default_factory=Path.cwd)

    @property
    def result_dir(self) -> Path:
        return self.root / self.raw["paths"]["result_dir"]

    @property
    def checker_database(self) -> Path:
        return self.root / self.raw["paths"]["checker_database"]

    @property
    def prompt_template(self) -> Path:
        return self.root / self.raw["paths"]["prompt_template"]

    @property
    def mock_kernel(self) -> Path:
        return self.root / self.raw["paths"]["mock_kernel"]

    @property
    def commits_file(self) -> Path:
        return self.root / self.raw["paths"]["commits_file"]

    @property
    def pipeline(self) -> dict[str, Any]:
        return self.raw["pipeline"]

    @property
    def llm(self) -> dict[str, Any]:
        return self.raw["llm"]

    @property
    def backend(self) -> dict[str, Any]:
        return self.raw["backend"]

    @property
    def visualization(self) -> dict[str, Any]:
        return self.raw["visualization"]


_config: AppConfig | None = None


def load_config(config_path: str | Path, root: str | Path | None = None) -> AppConfig:
    global _config
    config_path = Path(config_path)
    root_path = Path(root) if root else config_path.parent.parent
    with open(config_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    _config = AppConfig(raw=raw, root=root_path.resolve())
    _config.result_dir.mkdir(parents=True, exist_ok=True)
    return _config


def get_config() -> AppConfig:
    if _config is None:
        raise RuntimeError("配置未初始化，请先调用 load_config()")
    return _config


def load_llm_keys(keys_path: str | Path | None = None) -> dict[str, str]:
    if keys_path is None:
        keys_path = get_config().root / "config" / "llm_keys.yaml"
    keys_path = Path(keys_path)
    if not keys_path.exists():
        return {}
    with open(keys_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
