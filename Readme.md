# KNighter-Lab：LLM 辅助 Linux 内核缺陷静态检测

基于 SOSP'25 论文 [KNighter](https://arxiv.org/abs/2503.09002) 的课程实验框架，实现 LLM 自动生成 Clang Static Analyzer (CSA) checker 的完整流水线。

> 初期方案见 [Readme.md](Readme.md)

## 项目结构

```
软件质量保障/
├── config/                 # 配置文件
├── commits/                # 示例补丁数据
├── checker_database/       # 预置 checker 示例
├── data/mock_kernel/       # 模拟内核源码（轻量扫描）
├── prompt_template/        # LLM 提示词模板
├── src/                    # 核心代码
│   ├── main.py             # CLI 入口
│   ├── checker_gen.py      # Checker 合成流水线
│   ├── checker_refine.py   # 并行 Refine（ThreadPoolExecutor）
│   ├── checker_scan.py     # 轻量模块扫描
│   ├── checker_triage.py   # 报告分类
│   ├── visualize.py        # 可视化（rich + matplotlib）
│   └── backends/mock_csa.py
├── scripts/run_experiment.py
├── Dockerfile
└── docker-compose.yml
```

## 快速开始

### 本地运行

```bash
pip install -r requirements.txt
python scripts/run_experiment.py --full
```

### Docker 运行

```bash
docker-compose up --build
```

## 流水线模式

| 模式 | 命令 | 说明 |
|------|------|------|
| `gen` | `python src/main.py gen` | 从补丁合成 checker |
| `refine` | `python src/main.py refine` | 并行 refine 降低误报 |
| `scan` | `python src/main.py scan` | 扫描指定内核模块 |
| `visualize` | `python src/main.py visualize` | 生成实验图表 |
| `pipeline` | `python scripts/run_experiment.py --full` | 完整流水线 |

## 课程优化项

| 优化方向 | 配置项 | 说明 |
|----------|--------|------|
| 生成数量控制 | `checker_nums: 3` | 仅生成关键类型 checker |
| Refine 并行化 | `refine_parallel_jobs: 4` | ThreadPoolExecutor |
| 轻量扫描 | `scan_modules` | 仅扫描 kernel/sched 等 |
| 结果可视化 | `results/visualization/` | 饼图、柱状图、对比图 |

## 配置说明

- `config/config.yaml`：主流水线配置
- `config/llm_keys.yaml`：API 密钥（默认 `fake` 模式无需密钥）

将 `llm.provider` 改为 `openai` 并填入密钥即可使用真实 LLM。

## 输出产物

- `results/generated/<commit_id>/`：合成的 pattern、plan、checker
- `results/experiment_summary.json`：实验汇总数据
- `results/visualization/*.png`：可视化图表

## 参考文献

Chenyuan Yang et al. **KNighter: Transforming Static Analysis with LLM-Synthesized Checkers**, SOSP 2025.
