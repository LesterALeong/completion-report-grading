"""Construct the single allowlisted judge payload for one cell."""

from __future__ import annotations

from typing import Any

from .data import ROOT
from .reports import NEUTRAL_REPORT, PERSUASIVE_REPORT


COMMON_PROMPT = (ROOT / "prompts" / "common.md").read_text(encoding="utf-8").strip()
MITIGATION_PROMPT = (ROOT / "prompts" / "mitigation.md").read_text(encoding="utf-8").strip()


def build_prompt(case: dict[str, Any], condition: str) -> str:
    if condition not in {"report_free", "neutral", "persuasive", "mitigation"}:
        raise ValueError(f"unknown condition: {condition}")

    sections = [COMMON_PROMPT]
    if condition == "mitigation":
        sections.append(MITIGATION_PROMPT)
    sections.append(f"Task:\n{case['task']}")
    criteria = "\n".join(f"- {item['text']}" for item in case["criteria"])
    sections.append(f"Acceptance criteria:\n{criteria}")
    sections.append(f"Submitted code:\n```python\n{case['code'].rstrip()}\n```")
    if condition == "neutral":
        sections.append(f"Completion report:\n{NEUTRAL_REPORT}")
    elif condition == "persuasive" or condition == "mitigation":
        sections.append(f"Completion report:\n{PERSUASIVE_REPORT}")
    return "\n\n".join(sections)
