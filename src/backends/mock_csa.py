from __future__ import annotations

import hashlib
import random
import re
from pathlib import Path

from loguru import logger

from src.checker_data import ReportData
from src.global_config import get_config
from src.targets.mock_linux import MockLinuxTarget


class MockCSABackend:
    """模拟 Clang Static Analyzer 后端，用于课程实验端到端演示。"""

    def __init__(self):
        self.target = MockLinuxTarget()

    def build_checker(self, checker_code: str) -> tuple[bool, str]:
        if "SYNTAX_ERROR_DEMO" in checker_code or "was not declared" in checker_code:
            return False, "error: 'SYNTAX_ERROR_DEMO' was not declared in this scope"
        if "REGISTER_CHECKER" not in checker_code:
            return False, "error: missing REGISTER_CHECKER macro"
        return True, ""

    def validate_checker(
        self,
        checker_code: str,
        patch_data: dict,
    ) -> tuple[int, int]:
        """返回 (n_buggy, n_patched) 报告数。"""
        commit_id = patch_data["commit_id"]
        seed = int(hashlib.md5(commit_id.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        # 根据补丁类型模拟验证结果
        bug_type = patch_data.get("bug_type", "NPD")
        if bug_type in ("NPD", "Null-Pointer-Dereference"):
            n_buggy = rng.randint(1, 3)
            n_patched = rng.randint(0, 1)
        elif bug_type in ("UBI", "Use-Before-Initialization"):
            n_buggy = rng.randint(1, 2)
            n_patched = 0
        else:
            n_buggy = rng.randint(1, 2)
            n_patched = rng.randint(0, 2)

        valid_threshold = get_config().pipeline.get("valid_threshold", 50)
        if n_buggy <= n_patched or n_patched >= valid_threshold:
            n_buggy = max(n_buggy, n_patched + 1)

        logger.info(f"[MockCSA] Validation {commit_id}: buggy={n_buggy}, patched={n_patched}")
        return n_buggy, n_patched

    def run_checker(
        self,
        checker_code: str,
        patch_data: dict,
        modules: list[str] | None = None,
    ) -> list[ReportData]:
        modules = modules or get_config().pipeline.get("scan_modules", [])
        files = self.target.list_scan_files(modules)
        reports: list[ReportData] = []

        alloc_funcs = self._extract_target_funcs(checker_code, patch_data)
        seed = int(hashlib.md5(patch_data["commit_id"].encode()).hexdigest()[:8], 16)
        rng = random.Random(seed + 42)

        for fpath in files:
            content = fpath.read_text(encoding="utf-8")
            rel = str(fpath.relative_to(self.target.kernel_root)).replace("\\", "/")
            for i, line in enumerate(content.splitlines(), 1):
                for func in alloc_funcs:
                    if func in line and "if (!" not in line and "unlikely(!" not in line:
                        if rng.random() < 0.35:
                            reports.append(
                                ReportData(
                                    file=rel,
                                    line=i + rng.randint(1, 5),
                                    message=f"Potential null dereference: unchecked {func} return value",
                                    trace=[
                                        f"{func}() called at {rel}:{i}",
                                        f"Dereference without null check at {rel}:{i + 2}",
                                    ],
                                )
                            )
                if "use before init" in patch_data.get("bug_type", "").lower() or patch_data.get("bug_type") == "UBI":
                    if "__free" in line or "uninitialized" in content.lower():
                        if rng.random() < 0.2:
                            reports.append(
                                ReportData(
                                    file=rel,
                                    line=i,
                                    message="Variable used before initialization",
                                    trace=[f"Path without assignment at {rel}:{i}"],
                                )
                            )

        # 添加一个已知 FP 用于 refine 演示
        if reports:
            reports[0].trace.append("Note: nearby branch contains unlikely(!ptr) check")
        logger.info(f"[MockCSA] Scan found {len(reports)} reports in modules {modules}")
        return reports

    def _extract_target_funcs(self, checker_code: str, patch_data: dict) -> list[str]:
        funcs = []
        for f in ("devm_kzalloc", "kzalloc", "kmalloc", "devm_kmalloc"):
            if f in checker_code or f in patch_data.get("patch", ""):
                funcs.append(f)
        return funcs or ["devm_kzalloc"]

    def extract_reports_sample(
        self,
        reports: list[ReportData],
        sample_size: int = 5,
        seed: int = 0,
    ) -> list[ReportData]:
        if len(reports) <= sample_size:
            return list(reports)
        rng = random.Random(seed)
        return rng.sample(reports, sample_size)
