from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any

from loguru import logger

from src.global_config import get_config, load_llm_keys


class BaseLLMClient(ABC):
    @abstractmethod
    def chat(self, prompt: str, system: str = "") -> str:
        pass


class FakeLLMClient(BaseLLMClient):
    """课程实验用模拟 LLM，基于规则生成符合 KNighter 流程的输出。"""

    def chat(self, prompt: str, system: str = "") -> str:
        prompt_lower = prompt.lower()
        # 更具体的任务优先匹配，避免 plan2checker 等 prompt 误触发 pattern 分析
        if "compilation error" in prompt_lower or "fix the compilation" in prompt_lower:
            return self._repair_checker(prompt)
        if "classify as" in prompt_lower and "tp" in prompt_lower:
            return self._triage_report(prompt)
        if "refine the checker" in prompt_lower or (
            "false positive" in prompt_lower and "current checker" in prompt_lower
        ):
            return self._refine_checker(prompt)
        if "write a csa checker" in prompt_lower or "implementation plan" in prompt_lower and "checker template" in prompt_lower:
            return self._checker_generation(prompt)
        if "analyze the patch and find out" in prompt_lower:
            return self._pattern_analysis(prompt)
        if "elaborate plan" in prompt_lower or "organize an elaborate plan" in prompt_lower:
            return self._plan_synthesis(prompt)
        return self._generic_response(prompt)

    def _extract_alloc_func(self, prompt: str) -> str:
        for func in ("devm_kzalloc", "kzalloc", "kmalloc", "devm_kmalloc"):
            if func in prompt:
                return func
        return "devm_kzalloc"

    def _pattern_analysis(self, prompt: str) -> str:
        alloc = self._extract_alloc_func(prompt)
        return (
            f"## Bug Pattern\n\n"
            f"The bug pattern is the failure to check the return value of "
            f"`{alloc}()` for NULL before dereferencing it.\n\n"
            f"A potential null pointer may be caused by a failed memory allocation. "
            f"The fix adds a null check immediately after the allocation call."
        )

    def _plan_synthesis(self, prompt: str) -> str:
        alloc = self._extract_alloc_func(prompt)
        return (
            f"## Detection Plan\n\n"
            f"1. **Program State Management**: Use `PossibleNullPtrMap` to track "
            f"memory regions returned by `{alloc}`.\n"
            f"2. **checkPostCall**: After `{alloc}` calls, mark returned region as unchecked.\n"
            f"3. **checkBranchCondition**: Recognize `if (!ptr)`, `if (ptr == NULL)`, "
            f"and `if (unlikely(!ptr))` as valid null checks.\n"
            f"4. **checkBind**: Track pointer aliasing via `PtrAliasMap`.\n"
            f"5. **checkLocation**: Warn when dereferencing unchecked regions."
        )

    def _checker_generation(self, prompt: str, inject_syntax_error: bool = True) -> str:
        alloc = self._extract_alloc_func(prompt)
        code = _CHECKER_TEMPLATE.format(alloc=alloc)
        # 首次生成故意留语法错误，供 repair 阶段演示（论文 Figure 3）
        if inject_syntax_error and "SYNTAX_ERROR_DEMO" not in code:
            code = "SYNTAX_ERROR_DEMO;\n" + code
        return f"```cpp\n{code}\n```"

    def _repair_checker(self, prompt: str) -> str:
        alloc = self._extract_alloc_func(prompt)
        return self._checker_generation(prompt, inject_syntax_error=False)

    def _triage_report(self, prompt: str) -> str:
        if "unlikely" in prompt.lower() or "already checked" in prompt.lower():
            return json.dumps({"label": "FP", "reason": "Code contains valid null check via unlikely(!ptr)."})
        if "missing null check" in prompt.lower() or "no null check" in prompt.lower():
            return json.dumps({"label": "TP", "reason": "Missing null check after allocation, matches target pattern."})
        # 默认按采样比例
        line_match = re.search(r"line[:\s]+(\d+)", prompt, re.I)
        if line_match and int(line_match.group(1)) % 3 == 0:
            return json.dumps({"label": "FP", "reason": "Null check present in alternate branch."})
        return json.dumps({"label": "TP", "reason": "Report matches unchecked allocation pattern."})

    def _refine_checker(self, prompt: str) -> str:
        alloc = self._extract_alloc_func(prompt)
        code = _REFINED_CHECKER_TEMPLATE.format(alloc=alloc)
        return f"```cpp\n{code}\n```"

    def _generic_response(self, prompt: str) -> str:
        return "Analysis complete. See structured output above."


class OpenAILLMClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str, temperature: float = 0.2):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

    def chat(self, prompt: str, system: str = "") -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        return response.choices[0].message.content or ""


def create_llm_client() -> BaseLLMClient:
    cfg = get_config()
    provider = cfg.llm.get("provider", "fake")
    if provider == "openai":
        keys = load_llm_keys()
        api_key = keys.get("openai_api_key", "")
        if not api_key:
            logger.warning("未配置 OpenAI API Key，回退到 fake 模式")
            return FakeLLMClient()
        return OpenAILLMClient(
            api_key=api_key,
            model=cfg.llm.get("model", "gpt-4o-mini"),
            temperature=cfg.llm.get("temperature", 0.2),
        )
    return FakeLLMClient()


_CHECKER_TEMPLATE = '''// KNighter-synthesized checker for {alloc} null dereference
#include "clang/StaticAnalyzer/Core/BugReporter/BugType.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h"

using namespace clang;
using namespace ento;

namespace {{
class {alloc}NullChecker : public Checker<check::PostStmt<CallExpr>,
                                          check::BranchCondition,
                                          check::Location,
                                          check::Bind> {{
  mutable std::unique_ptr<BugType> BT;

public:
  {alloc}NullChecker() : BT(new BugType(this, "{alloc} null dereference", "Null Dereference")) {{}}

  void checkPostCall(const CallEvent &Call, CheckerContext &C) const;
  void checkBranchCondition(const Stmt *Cond, CheckerContext &C) const;
  void checkLocation(SVal Loc, bool IsLoad, const Stmt *S, CheckerContext &C) const;
  void checkBind(SVal Loc, SVal Val, const Stmt *S, CheckerContext &C) const;
}};
}}

REGISTER_CHECKER({alloc}NullChecker)
'''

_REFINED_CHECKER_TEMPLATE = '''// KNighter-refined checker for {alloc} null dereference
#include "clang/StaticAnalyzer/Core/BugReporter/BugType.h"
#include "clang/StaticAnalyzer/Core/PathSensitive/CheckerContext.h"

using namespace clang;
using namespace ento;

namespace {{
class {alloc}NullChecker : public Checker<check::PostStmt<CallExpr>,
                                          check::BranchCondition,
                                          check::Location,
                                          check::Bind> {{
  mutable std::unique_ptr<BugType> BT;

public:
  {alloc}NullChecker() : BT(new BugType(this, "{alloc} null dereference", "Null Dereference")) {{}}

  void checkPostCall(const CallEvent &Call, CheckerContext &C) const;
  void checkBranchCondition(const Stmt *Cond, CheckerContext &C) const;
  void checkLocation(SVal Loc, bool IsLoad, const Stmt *S, CheckerContext &C) const;
  void checkBind(SVal Loc, SVal Val, const Stmt *S, CheckerContext &C) const;

private:
  bool isValidNullCheck(const Stmt *Cond) const;  // handles unlikely(!ptr)
}};
}}

REGISTER_CHECKER({alloc}NullChecker)
'''
