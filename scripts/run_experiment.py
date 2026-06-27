#!/usr/bin/env python3
"""课程实验一键运行脚本。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from loguru import logger


def main():
    parser = argparse.ArgumentParser(description="KNighter-Lab 课程实验")
    parser.add_argument("--config", default="config/config.yaml", help="配置文件路径")
    parser.add_argument("--full", action="store_true", help="运行完整流水线")
    parser.add_argument("--mode", choices=["gen", "refine", "scan", "visualize", "pipeline"],
                        default="pipeline", help="运行模式")
    args = parser.parse_args()

    logger.remove()
    logger.add(sys.stderr, level="INFO",
               format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}")

    from src.global_config import load_config
    from src.main import CLI

    load_config(ROOT / args.config, root=ROOT)
    cli = CLI(config=args.config)

    mode = "pipeline" if args.full else args.mode
    logger.info(f"KNighter-Lab 启动，模式={mode}")

    if mode == "gen":
        cli.gen()
    elif mode == "refine":
        cli.refine()
    elif mode == "scan":
        cli.scan()
    elif mode == "visualize":
        cli.visualize()
    else:
        cli.pipeline()

    logger.success("实验完成！结果见 results/ 目录")


if __name__ == "__main__":
    main()
