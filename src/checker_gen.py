from __future__ import annotations

from pathlib import Path

from loguru import logger

from src import agent
from src.backends.mock_csa import MockCSABackend
from src.checker_data import CheckerData, CheckerStatus
from src.global_config import get_config
from src.model import create_llm_client
from src.targets.mock_linux import MockLinuxTarget
from src.tools import ensure_dir


class CheckerGenerator:
    def __init__(self):
        self.cfg = get_config()
        self.client = create_llm_client()
        self.backend = MockCSABackend()
        self.target = MockLinuxTarget()

    def generate_all(self) -> list[CheckerData]:
        commits = self.target.load_commits()
        limit = self.cfg.pipeline.get("checker_nums", 3)
        commits = commits[:limit]
        results: list[CheckerData] = []
        for patch_data in commits:
            try:
                checker = self.generate_one(patch_data)
                results.append(checker)
            except Exception as e:
                logger.error(f"生成失败 {patch_data['commit_id']}: {e}")
                failed = CheckerData(
                    commit_id=patch_data["commit_id"],
                    bug_type=patch_data.get("bug_type", "unknown"),
                    status=CheckerStatus.FAILED,
                )
                results.append(failed)
        return results

    def generate_one(self, patch_data: dict) -> CheckerData:
        commit_id = patch_data["commit_id"]
        out_dir = ensure_dir(self.cfg.result_dir / "generated" / commit_id)
        logger.info(f"=== Checker Synthesis: {commit_id} ===")

        data = CheckerData(
            commit_id=commit_id,
            bug_type=patch_data.get("bug_type", "NPD"),
            status=CheckerStatus.GENERATING,
            output_dir=str(out_dir),
        )

        max_iter = self.cfg.pipeline.get("max_iterations", 3)
        max_repair = self.cfg.pipeline.get("max_repair_attempts", 5)

        for iteration in range(1, max_iter + 1):
            logger.info(f"--- Iteration {iteration}/{max_iter} ---")

            # Stage 1: Pattern Analysis
            data.pattern = agent.patch2pattern(self.client, patch_data)

            # Stage 2: Plan Synthesis
            data.plan = agent.pattern2plan(self.client, patch_data, data.pattern)

            # Stage 3: Checker Implementation
            data.checker_code = agent.plan2checker(
                self.client, patch_data, data.pattern, data.plan
            )

            # Stage 3b: Syntax Repair
            for attempt in range(max_repair):
                ok, err = self.backend.build_checker(data.checker_code)
                if ok:
                    break
                logger.warning(f"编译错误 (attempt {attempt + 1}): {err}")
                data.checker_code = agent.repair_checker(self.client, data.checker_code, err)
            else:
                logger.warning(f"编译修复失败，继续下一轮迭代")
                continue

            # Stage 4: Validation
            n_buggy, n_patched = self.backend.validate_checker(data.checker_code, patch_data)
            data.n_buggy = n_buggy
            data.n_patched = n_patched

            if n_buggy > n_patched:
                data.status = CheckerStatus.VALID
                logger.success(f"Valid checker synthesized for {commit_id}")
                data.save(out_dir)
                return data

        data.status = CheckerStatus.INVALID
        data.save(out_dir)
        logger.error(f"Failed to synthesize valid checker for {commit_id}")
        return data
