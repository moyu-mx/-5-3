from __future__ import annotations

from loguru import logger

from src import agent
from src.checker_data import ReportData
from src.model import create_llm_client


class TriageEngine:
    def __init__(self):
        self.client = create_llm_client()

    def triage_reports(
        self,
        reports: list[ReportData],
        patch_data: dict,
        pattern: str,
    ) -> list[ReportData]:
        results = []
        for report in reports:
            triaged = self.triage_one(report, patch_data, pattern)
            results.append(triaged)
        tp = sum(1 for r in results if r.triage_label == "TP")
        fp = sum(1 for r in results if r.triage_label == "FP")
        logger.info(f"[Triage] TP={tp}, FP={fp} (sample={len(reports)})")
        return results

    def triage_one(
        self,
        report: ReportData,
        patch_data: dict,
        pattern: str,
    ) -> ReportData:
        report_dict = {
            "file": report.file,
            "line": report.line,
            "message": report.message,
            "trace": report.trace,
        }
        result = agent.triage_report(self.client, patch_data, pattern, report_dict)
        report.triage_label = result.get("label", "unknown")
        report.triage_reason = result.get("reason", "")
        return report
