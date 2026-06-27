from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from loguru import logger

from src import agent
from src.backends.mock_csa import MockCSABackend
from src.checker_data import CheckerData, CheckerStatus, RefineAttempt
from src.checker_triage import TriageEngine
from src.global_config import get_config
from src.model import create_llm_client


class CheckerRefiner:
    def __init__(self):
        self.cfg = get_config()
        self.client = create_llm_client()
        self.backend = MockCSABackend()
        self.triage = TriageEngine()

    def refine_all(self, checkers: list[CheckerData], parallel: bool = True) -> list[CheckerData]:
        valid = [c for c in checkers if c.status == CheckerStatus.VALID]
        if not valid:
            logger.warning("没有 valid checker 可供 refine")
            return checkers

        jobs = self.cfg.pipeline.get("refine_parallel_jobs", 4)
        logger.info(f"开始并行 refine，workers={jobs}, checkers={len(valid)}")

        refined_map: dict[str, CheckerData] = {}
        if parallel and len(valid) > 1:
            with ThreadPoolExecutor(max_workers=jobs) as executor:
                futures = {
                    executor.submit(self.refine_one, c): c.commit_id for c in valid
                }
                for future in as_completed(futures):
                    cid = futures[future]
                    try:
                        refined_map[cid] = future.result()
                    except Exception as e:
                        logger.error(f"Refine 失败 {cid}: {e}")
        else:
            for c in valid:
                refined_map[c.commit_id] = self.refine_one(c)

        result = []
        for c in checkers:
            result.append(refined_map.get(c.commit_id, c))
        return result

    def refine_one(self, data: CheckerData) -> CheckerData:
        from src.targets.mock_linux import MockLinuxTarget

        target = MockLinuxTarget()
        patch_data = target.get_patch(data.commit_id, target.load_commits())
        if not patch_data:
            data.status = CheckerStatus.FAILED
            return data

        out_dir = Path(data.output_dir) if data.output_dir else (
            self.cfg.result_dir / "generated" / data.commit_id
        )
        data.status = CheckerStatus.REFINING
        max_iter = self.cfg.pipeline.get("refine_max_iterations", 3)
        plausible_threshold = self.cfg.pipeline.get("plausible_threshold", 20)
        modules = self.cfg.pipeline.get("scan_modules", [])

        for iteration in range(1, max_iter + 1):
            logger.info(f"[{data.commit_id}] Refine iteration {iteration}")

            reports = self.backend.run_checker(data.checker_code, patch_data, modules)
            data.total_reports = len(reports)
            data.reports = reports

            sample = self.backend.extract_reports_sample(
                reports,
                sample_size=self.cfg.pipeline.get("triage_sample_size", 5),
                seed=iteration,
            )
            triaged = self.triage.triage_reports(sample, patch_data, data.pattern)
            fp_reports = [r for r in triaged if r.triage_label == "FP"]
            tp_count = sum(1 for r in triaged if r.triage_label == "TP")
            fp_count = len(fp_reports)
            fp_rate = fp_count / max(len(triaged), 1)
            data.fp_rate = round(fp_rate, 3)

            attempt = RefineAttempt(
                iteration=iteration,
                total_reports=len(reports),
                fp_count=fp_count,
                tp_count=tp_count,
                accepted=False,
            )

            if len(reports) < plausible_threshold or fp_count <= 1:
                attempt.accepted = True
                data.refine_attempts.append(attempt)
                data.status = CheckerStatus.PLAUSIBLE
                logger.success(
                    f"[{data.commit_id}] Plausible checker "
                    f"(reports={len(reports)}, fp_rate={data.fp_rate})"
                )
                data.save(out_dir)
                return data

            # Refine based on FPs
            fp_dicts = [
                {"file": r.file, "line": r.line, "message": r.message, "reason": r.triage_reason}
                for r in fp_reports
            ]
            data.checker_code = agent.refine_checker(
                self.client, data.checker_code, data.pattern, fp_dicts
            )
            n_buggy, n_patched = self.backend.validate_checker(data.checker_code, patch_data)
            data.n_buggy = n_buggy
            data.n_patched = n_patched

            if n_buggy <= n_patched:
                attempt.notes = "Refinement broke validity"
                data.refine_attempts.append(attempt)
                break

            attempt.notes = f"Refined to handle {fp_count} FPs"
            data.refine_attempts.append(attempt)

        if data.status != CheckerStatus.PLAUSIBLE:
            data.status = CheckerStatus.VALID
        data.save(out_dir)
        return data
