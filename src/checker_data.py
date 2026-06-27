from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class CheckerStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    VALID = "valid"
    INVALID = "invalid"
    REFINING = "refining"
    PLAUSIBLE = "plausible"
    FAILED = "failed"


@dataclass
class ReportData:
    file: str
    line: int
    message: str
    trace: list[str] = field(default_factory=list)
    triage_label: str = ""  # TP | FP | unknown
    triage_reason: str = ""


@dataclass
class RefineAttempt:
    iteration: int
    total_reports: int
    fp_count: int
    tp_count: int
    accepted: bool
    notes: str = ""


@dataclass
class CheckerData:
    commit_id: str
    bug_type: str
    status: CheckerStatus = CheckerStatus.PENDING
    pattern: str = ""
    plan: str = ""
    checker_code: str = ""
    output_dir: str = ""
    n_buggy: int = 0
    n_patched: int = 0
    total_reports: int = 0
    fp_rate: float = 0.0
    refine_attempts: list[RefineAttempt] = field(default_factory=list)
    reports: list[ReportData] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def save(self, base_dir: Path) -> None:
        base_dir = Path(base_dir)
        base_dir.mkdir(parents=True, exist_ok=True)
        (base_dir / "pattern.md").write_text(self.pattern, encoding="utf-8")
        (base_dir / "plan.md").write_text(self.plan, encoding="utf-8")
        (base_dir / "checker.cpp").write_text(self.checker_code, encoding="utf-8")
        meta = asdict(self)
        meta["status"] = self.status.value
        meta["refine_attempts"] = [asdict(a) for a in self.refine_attempts]
        meta["reports"] = [asdict(r) for r in self.reports]
        with open(base_dir / "metadata.yaml", "w", encoding="utf-8") as f:
            yaml.dump(meta, f, allow_unicode=True, default_flow_style=False)

    @classmethod
    def load(cls, base_dir: Path) -> CheckerData:
        base_dir = Path(base_dir)
        with open(base_dir / "metadata.yaml", encoding="utf-8") as f:
            meta = yaml.safe_load(f)
        data = cls(
            commit_id=meta["commit_id"],
            bug_type=meta["bug_type"],
            status=CheckerStatus(meta["status"]),
            pattern=(base_dir / "pattern.md").read_text(encoding="utf-8"),
            plan=(base_dir / "plan.md").read_text(encoding="utf-8"),
            checker_code=(base_dir / "checker.cpp").read_text(encoding="utf-8"),
            output_dir=str(base_dir),
            n_buggy=meta.get("n_buggy", 0),
            n_patched=meta.get("n_patched", 0),
            total_reports=meta.get("total_reports", 0),
            fp_rate=meta.get("fp_rate", 0.0),
            created_at=meta.get("created_at", ""),
        )
        data.refine_attempts = [RefineAttempt(**a) for a in meta.get("refine_attempts", [])]
        data.reports = [ReportData(**r) for r in meta.get("reports", [])]
        return data


def save_experiment_summary(results: list[CheckerData], output_path: Path) -> None:
    summary = {
        "generated_at": datetime.now().isoformat(),
        "total_checkers": len(results),
        "valid_count": sum(1 for r in results if r.status in (CheckerStatus.VALID, CheckerStatus.PLAUSIBLE, CheckerStatus.REFINING)),
        "plausible_count": sum(1 for r in results if r.status == CheckerStatus.PLAUSIBLE),
        "failed_count": sum(1 for r in results if r.status == CheckerStatus.FAILED),
        "avg_fp_rate": round(sum(r.fp_rate for r in results) / max(len(results), 1), 3),
        "checkers": [
            {
                "commit_id": r.commit_id,
                "bug_type": r.bug_type,
                "status": r.status.value,
                "n_buggy": r.n_buggy,
                "n_patched": r.n_patched,
                "total_reports": r.total_reports,
                "fp_rate": r.fp_rate,
            }
            for r in results
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
