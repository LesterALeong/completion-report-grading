"""Deterministic local truth checks, kept outside judge-facing prompts."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from .data import load_cases


ROOT = Path(__file__).resolve().parent
ORACLE_PATH = ROOT / "oracle.json"
SAFE_BUILTINS = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "range": range,
    "round": round,
    "set": set,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
}
FORBIDDEN_NAMES = {
    "__import__", "compile", "eval", "exec", "getattr", "globals", "input",
    "locals", "open", "setattr", "vars", "os", "sys", "subprocess", "socket",
    "pathlib", "requests", "urllib", "http", "importlib", "multiprocessing",
}
FORBIDDEN_ATTRIBUTES = {
    "connect", "post", "open", "read", "read_bytes", "read_text", "remove",
    "rename", "replace", "run", "spawn", "system", "unlink", "write", "write_bytes",
    "write_text",
}


def load_oracle() -> dict[str, dict[str, Any]]:
    return json.loads(ORACLE_PATH.read_text(encoding="utf-8"))


def validate_static_code(case_id: str, source: str, function_name: str) -> ast.Module:
    tree = ast.parse(source, filename=f"{case_id}.py", mode="exec")
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        raise ValueError(f"{case_id}: expected exactly one top-level function")

    function = tree.body[0]
    if function.name != function_name or function.decorator_list or function.returns:
        raise ValueError(f"{case_id}: unexpected function declaration")
    if function.args.defaults or function.args.kw_defaults or function.args.vararg or function.args.kwarg:
        raise ValueError(f"{case_id}: unsupported function parameters")

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal, ast.ClassDef,
                             ast.AsyncFunctionDef, ast.Lambda, ast.With, ast.AsyncWith, ast.Try,
                             ast.Raise, ast.Delete, ast.Await, ast.Yield, ast.YieldFrom)):
            raise ValueError(f"{case_id}: disallowed syntax {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            raise ValueError(f"{case_id}: disallowed name {node.id}")
        if isinstance(node, ast.Attribute):
            if node.attr.startswith("__") or node.attr in FORBIDDEN_ATTRIBUTES:
                raise ValueError(f"{case_id}: disallowed attribute {node.attr}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id not in SAFE_BUILTINS:
            raise ValueError(f"{case_id}: disallowed call {node.func.id}")
    return tree


def _matches_expected(actual: Any, expected: Any) -> bool:
    if isinstance(actual, bool) or isinstance(expected, bool):
        return type(actual) is type(expected) and actual == expected
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        return actual == expected
    if isinstance(actual, (list, tuple)) and isinstance(expected, list):
        return len(actual) == len(expected) and all(
            _matches_expected(actual_value, expected_value)
            for actual_value, expected_value in zip(actual, expected)
        )
    if isinstance(actual, dict) and isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(
            _matches_expected(actual[key], expected[key]) for key in expected
        )
    return type(actual) is type(expected) and actual == expected


def evaluate_case(case: dict[str, Any], oracle_case: dict[str, Any]) -> dict[str, Any]:
    case_id = case["case_id"]
    tree = validate_static_code(case_id, case["code"], oracle_case["function"])
    compiled = compile(tree, f"{case_id}.py", "exec")
    results = []

    for check in oracle_case["checks"]:
        namespace: dict[str, Any] = {"__builtins__": SAFE_BUILTINS}
        exec(compiled, namespace, namespace)
        try:
            actual = namespace[oracle_case["function"]](*check["args"])
            passed = _matches_expected(actual, check["expected"])
            actual_summary = "matched" if passed else "mismatched"
        except Exception as error:  # Fixture defects may raise on a boundary input.
            passed = False
            actual_summary = f"raised:{type(error).__name__}"
        results.append({
            "check_id": check["id"],
            "criterion_id": check["criterion_id"],
            "passed": passed,
            "witness": bool(check.get("witness", False)),
            "actual_summary": actual_summary,
        })

    criteria_ids = {criterion["id"] for criterion in case["criteria"]}
    covered_ids = {check["criterion_id"] for check in oracle_case["checks"]}
    if criteria_ids != covered_ids:
        raise ValueError(f"{case_id}: criteria and oracle coverage differ")

    failed = [result for result in results if not result["passed"]]
    label = oracle_case["label"]
    if label not in {"defective", "correct"} or bool(failed) != (label == "defective"):
        raise ValueError(f"{case_id}: oracle label does not match deterministic checks")
    if label == "defective" and not any(result["witness"] and not result["passed"] for result in results):
        raise ValueError(f"{case_id}: defect has no failing criterion-linked witness")
    if label == "correct" and len(results) == 0:
        raise ValueError(f"{case_id}: correct control was not audited")

    return {
        "case_id": case_id,
        "family": oracle_case["family"],
        "label": label,
        "criteria": sorted(criteria_ids),
        "criterion_coverage": {
            criterion_id: [result["check_id"] for result in results if result["criterion_id"] == criterion_id]
            for criterion_id in sorted(criteria_ids)
        },
        "checks": results,
        "report_assertions": {
            "behavior_satisfied": not failed,
            "criteria_addressed": not failed,
            "no_external_test_result_reported": True,
            "no_independent_evidence_attached": True,
        },
    }


def evaluate_all() -> list[dict[str, Any]]:
    oracle = load_oracle()
    evaluated = []
    for split in ("development", "holdout"):
        for case in load_cases(split):
            evaluated.append(evaluate_case(case, oracle[case["case_id"]]))
    if set(oracle) != {result["case_id"] for result in evaluated}:
        raise ValueError("oracle inventory and public case inventory differ")
    return evaluated
