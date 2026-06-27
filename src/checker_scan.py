from __future__ import annotations

from pathlib import Path

from loguru import logger

from src.backends.mock_csa import MockCSABackend
from src.checker_data import CheckerData, ReportData
from src.global_config import get_config
from src.targets.mock_linux import MockLinuxTarget


class ScanEngine:
    def __init__(self):
        self.cfg = get_config()
        self.backend = MockCSABackend()
        self.target = MockLinuxTarget()

    def scan_checker(self, data: CheckerData) -> list[ReportData]:
        patch_data = self.target.get_patch(data.commit_id, self.target.load_commits())
        if not patch_data:
            return []
        modules = self.cfg.pipeline.get("scan_modules", [])
        logger.info(f"[Scan] {data.commit_id} on modules: {modules}")
        reports = self.backend.run_checker(data.checker_code, patch_data, modules)
        data.reports = reports
        data.total_reports = len(reports)
        if data.output_dir:
            data.save(Path(data.output_dir))
        return reports

    def scan_all(self, checkers: list[CheckerData]) -> dict[str, list[ReportData]]:
        results = {}
        for c in checkers:
            if c.status in (CheckerStatus.VALID, CheckerStatus.PLAUSIBLE) or c.checker_code:
                results[c.commit_id] = self.scan_checker(c)
        return results


from src.checker_data import CheckerStatus  # noqa: E402
