#!/usr/bin/env python3
"""KNighter-Lab CLI 入口。"""

from __future__ import annotations

import sys
from pathlib import Path

import fire
from loguru import logger

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.checker_data import CheckerData, save_experiment_summary
from src.checker_gen import CheckerGenerator
from src.checker_refine import CheckerRefiner
from src.checker_scan import ScanEngine
from src.global_config import load_config
from src.visualize import generate_charts, print_summary_table


class CLI:
    def __init__(self, config: str = "config/config.yaml"):
        self.config_path = config
        load_config(ROOT / config, root=ROOT)
        logger.remove()
        logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}")

    def gen(self):
        """从补丁生成 checker。"""
        gen = CheckerGenerator()
        results = gen.generate_all()
        print_summary_table(results)
        return results

    def refine(self, input_dir: str = "results/generated"):
        """并行 refine 已生成的 checker。"""
        input_path = ROOT / input_dir
        checkers = []
        for d in sorted(input_path.iterdir()):
            if d.is_dir() and (d / "metadata.yaml").exists():
                checkers.append(CheckerData.load(d))
        refiner = CheckerRefiner()
        results = refiner.refine_all(checkers)
        print_summary_table(results)
        return results

    def scan(self, input_dir: str = "results/generated"):
        """轻量扫描指定内核模块。"""
        input_path = ROOT / input_dir
        checkers = []
        for d in sorted(input_path.iterdir()):
            if d.is_dir() and (d / "metadata.yaml").exists():
                checkers.append(CheckerData.load(d))
        engine = ScanEngine()
        results = engine.scan_all(checkers)
        logger.info(f"扫描完成，共 {sum(len(v) for v in results.values())} 条报告")
        return results

    def visualize(self, input_dir: str = "results/generated"):
        """生成可视化图表。"""
        from src.global_config import get_config

        cfg = get_config()
        input_path = ROOT / input_dir
        checkers = []
        for d in sorted(input_path.iterdir()):
            if d.is_dir() and (d / "metadata.yaml").exists():
                checkers.append(CheckerData.load(d))
        out_dir = cfg.visualization.get("output_dir", "results/visualization")
        paths = generate_charts(checkers, ROOT / out_dir)
        print_summary_table(checkers)
        logger.info(f"图表已保存至 {ROOT / out_dir}")
        return paths

    def pipeline(self):
        """运行完整流水线：gen → refine → scan → visualize。"""
        gen_results = self.gen()
        refiner = CheckerRefiner()
        refined = refiner.refine_all(gen_results)
        engine = ScanEngine()
        engine.scan_all(refined)
        from src.global_config import get_config

        cfg = get_config()
        save_experiment_summary(refined, ROOT / cfg.result_dir / "experiment_summary.json")
        self.visualize()
        return refined


def main():
    fire.Fire(CLI)


if __name__ == "__main__":
    main()
