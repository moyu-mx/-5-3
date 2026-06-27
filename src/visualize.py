from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from loguru import logger
from rich.console import Console
from rich.table import Table

from src.checker_data import CheckerData, CheckerStatus

console = Console()

# 支持中文显示
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def print_summary_table(checkers: list[CheckerData]) -> None:
    table = Table(title="KNighter-Lab 实验结果汇总")
    table.add_column("Commit ID", style="cyan")
    table.add_column("Bug Type", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("N_buggy", justify="right")
    table.add_column("N_patched", justify="right")
    table.add_column("Reports", justify="right")
    table.add_column("FP Rate", justify="right")

    for c in checkers:
        table.add_row(
            c.commit_id[:12],
            c.bug_type,
            c.status.value,
            str(c.n_buggy),
            str(c.n_patched),
            str(c.total_reports),
            f"{c.fp_rate:.1%}" if c.fp_rate else "-",
        )
    console.print(table)


def generate_charts(checkers: list[CheckerData], output_dir: Path) -> list[Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    # 1. Checker 状态分布饼图
    status_counts: dict[str, int] = {}
    for c in checkers:
        status_counts[c.status.value] = status_counts.get(c.status.value, 0) + 1

    fig, ax = plt.subplots(figsize=(8, 6))
    labels = list(status_counts.keys())
    sizes = list(status_counts.values())
    colors = ["#4CAF50", "#2196F3", "#FF9800", "#F44336", "#9E9E9E"]
    ax.pie(sizes, labels=labels, autopct="%1.1f%%", colors=colors[: len(labels)], startangle=90)
    ax.set_title("Checker 合成状态分布")
    pie_path = output_dir / "checker_status_pie.png"
    fig.savefig(pie_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    paths.append(pie_path)
    logger.info(f"生成饼图: {pie_path}")

    # 2. 各 checker 报告数柱状图
    fig, ax = plt.subplots(figsize=(10, 6))
    commits = [c.commit_id[:10] for c in checkers]
    reports = [c.total_reports for c in checkers]
    colors_bar = ["#4CAF50" if c.status == CheckerStatus.PLAUSIBLE else "#2196F3" for c in checkers]
    ax.bar(commits, reports, color=colors_bar)
    ax.set_xlabel("Commit ID")
    ax.set_ylabel("Bug Reports")
    ax.set_title("各 Checker 扫描报告数量")
    ax.tick_params(axis="x", rotation=30)
    bar_path = output_dir / "scan_reports_bar.png"
    fig.savefig(bar_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    paths.append(bar_path)
    logger.info(f"生成柱状图: {bar_path}")

    # 3. 验证对比图 (N_buggy vs N_patched)
    fig, ax = plt.subplots(figsize=(10, 6))
    x = range(len(checkers))
    width = 0.35
    ax.bar([i - width / 2 for i in x], [c.n_buggy for c in checkers], width, label="N_buggy", color="#F44336")
    ax.bar([i + width / 2 for i in x], [c.n_patched for c in checkers], width, label="N_patched", color="#4CAF50")
    ax.set_xticks(list(x))
    ax.set_xticklabels([c.commit_id[:10] for c in checkers], rotation=30)
    ax.set_ylabel("Report Count")
    ax.set_title("Checker 验证：Buggy vs Patched 报告对比")
    ax.legend()
    val_path = output_dir / "validation_comparison.png"
    fig.savefig(val_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    paths.append(val_path)
    logger.info(f"生成验证对比图: {val_path}")

    # 4. FP Rate 折线图
    plausible = [c for c in checkers if c.fp_rate > 0]
    if plausible:
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(
            [c.commit_id[:10] for c in plausible],
            [c.fp_rate for c in plausible],
            marker="o",
            color="#FF9800",
            linewidth=2,
        )
        ax.set_ylabel("False Positive Rate")
        ax.set_title("Refine 后误报率")
        ax.tick_params(axis="x", rotation=30)
        ax.axhline(y=0.2, color="r", linestyle="--", alpha=0.5, label="20% threshold")
        ax.legend()
        fp_path = output_dir / "fp_rate_line.png"
        fig.savefig(fp_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        paths.append(fp_path)

    return paths
