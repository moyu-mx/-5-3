from __future__ import annotations

import re

from loguru import logger

from src.model import BaseLLMClient
from src.tools import extract_function_from_patch, load_knowledge, render_template


def extract_code_block(text: str) -> str:
    match = re.search(r"```(?:cpp|c)?\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def patch2pattern(client: BaseLLMClient, patch_data: dict) -> str:
    patch = patch_data.get("patch", "")
    message = patch_data.get("message", "")
    function_code = patch_data.get("function_code", extract_function_from_patch(patch))
    prompt = render_template(
        "patch2pattern.md",
        input_patch=patch,
        commit_message=message,
        function_code=function_code,
    )
    logger.info(f"[Agent] Pattern Analysis for {patch_data.get('commit_id', 'unknown')}")
    return client.chat(prompt)


def pattern2plan(client: BaseLLMClient, patch_data: dict, pattern: str) -> str:
    utility = load_knowledge("utility.md")
    suggestions = load_knowledge("suggestions.md")
    prompt = render_template(
        "pattern2plan.md",
        input_patch=patch_data.get("patch", ""),
        input_pattern=pattern,
        utility_functions=utility,
        suggestions=suggestions,
    )
    logger.info("[Agent] Plan Synthesis")
    return client.chat(prompt)


def plan2checker(client: BaseLLMClient, patch_data: dict, pattern: str, plan: str) -> str:
    template = load_knowledge("template.md")
    utility = load_knowledge("utility.md")
    prompt = render_template(
        "plan2checker.md",
        input_patch=patch_data.get("patch", ""),
        input_pattern=pattern,
        input_plan=plan,
        checker_template=template,
        utility_functions=utility,
    )
    logger.info("[Agent] Checker Generation")
    raw = client.chat(prompt)
    return extract_code_block(raw)


def repair_checker(client: BaseLLMClient, checker_code: str, error_msg: str) -> str:
    prompt = render_template(
        "repair_checker.md",
        checker_code=checker_code,
        compilation_error=error_msg,
    )
    logger.info("[Agent] Syntax Repair")
    raw = client.chat(prompt)
    return extract_code_block(raw)


def triage_report(client: BaseLLMClient, patch_data: dict, pattern: str, report: dict) -> dict:
    prompt = render_template(
        "triage_report.md",
        input_patch=patch_data.get("patch", ""),
        input_pattern=pattern,
        input_report=report,
    )
    logger.debug(f"[Agent] Triage report at {report.get('file')}:{report.get('line')}")
    raw = client.chat(prompt)
    import json

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        label = "FP" if "FP" in raw else "TP"
        return {"label": label, "reason": raw[:200]}


def refine_checker(client: BaseLLMClient, checker_code: str, pattern: str, fp_reports: list[dict]) -> str:
    prompt = render_template(
        "refine_checker.md",
        checker_code=checker_code,
        input_pattern=pattern,
        false_positives=fp_reports,
    )
    logger.info(f"[Agent] Checker Refinement ({len(fp_reports)} FPs)")
    raw = client.chat(prompt)
    return extract_code_block(raw)
