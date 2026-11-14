"""Score the checked-in development fixture pairs against their frozen examples.

The fixtures are authored and trusted. The AST checks narrow their syntax but do not
make Python execution a sandbox.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any


FOLLOWUP_DIR = Path(__file__).resolve().parent
ROOT = FOLLOWUP_DIR.parents[1]
INVENTORY_PATH = FOLLOWUP_DIR / "cases.json"
CASES_DIR = FOLLOWUP_DIR / "cases"
RESULTS_DIR = FOLLOWUP_DIR / "results"
SCREEN_SUMMARY_PATH = RESULTS_DIR / "screen-summary.json"
EXPECTED_CASE_COUNT = 6
EXPECTED_FIXTURE_COUNT = 12
SAFE_BUILTINS = {
    "enumerate": enumerate,
    "len": len,
    "range": range,
    "set": set,
    "sorted": sorted,
}
PURE_METHODS = {"count", "get", "join", "replace", "split", "strip"}
ALLOWED_AST_NODES = {
    ast.Add,
    ast.And,
    ast.Attribute,
    ast.BitOr,
    ast.BinOp,
    ast.BoolOp,
    ast.Call,
    ast.Compare,
    ast.comprehension,
    ast.Constant,
    ast.Dict,
    ast.DictComp,
    ast.Eq,
    ast.Expression,
    ast.FunctionDef,
    ast.GeneratorExp,
    ast.Gt,
    ast.GtE,
    ast.IfExp,
    ast.In,
    ast.Is,
    ast.IsNot,
    ast.List,
    ast.ListComp,
    ast.Load,
    ast.Lt,
    ast.LtE,
    ast.Module,
    ast.Mult,
    ast.Mod,
    ast.Name,
    ast.Not,
    ast.NotEq,
    ast.NotIn,
    ast.Or,
    ast.Return,
    ast.Set,
    ast.SetComp,
    ast.Slice,
    ast.Store,
    ast.Sub,
    ast.Subscript,
    ast.Tuple,
    ast.USub,
    ast.UAdd,
    ast.UnaryOp,
    ast.arg,
    ast.arguments,
}
TOP_LEVEL_KEYS = {"schema_version", "scope", "case_count", "fixture_file_count", "fixture_paths", "cases"}
CASE_KEYS = {
    "case_id", "family", "function_name", "parameters", "requirement", "flaw_rationale",
    "correct_path", "flawed_path", "visible_examples", "contract_checks",
}
VISIBLE_CHECK_KEYS = {"check_id", "input", "expected"}
CONTRACT_CHECK_KEYS = VISIBLE_CHECK_KEYS | {"witness"}


def _reject_nonstandard_json(value: str) -> None:
    raise ValueError(f"nonstandard JSON constant: {value}")


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_inventory() -> dict[str, Any]:
    return json.loads(
        INVENTORY_PATH.read_text(encoding="utf-8"),
        parse_constant=_reject_nonstandard_json,
    )


def validate_inventory(inventory: dict[str, Any]) -> None:
    if not isinstance(inventory, dict):
        raise ValueError("inventory must be a JSON object")
    if set(inventory) != TOP_LEVEL_KEYS:
        raise ValueError("inventory has unexpected or missing top-level fields")
    if inventory["schema_version"] != 1 or inventory["scope"] != "development_only":
        raise ValueError("inventory schema version or scope is invalid")
    cases = inventory["cases"]
    if not isinstance(cases, list) or len(cases) != EXPECTED_CASE_COUNT:
        raise ValueError(f"inventory must contain exactly {EXPECTED_CASE_COUNT} cases")
    if inventory["case_count"] != EXPECTED_CASE_COUNT:
        raise ValueError("inventory case_count does not match the frozen count")
    if inventory["fixture_file_count"] != EXPECTED_FIXTURE_COUNT:
        raise ValueError("inventory fixture_file_count does not match the frozen count")

    case_ids: set[str] = set()
    families: set[str] = set()
    expected_paths: list[str] = []
    for case in cases:
        if not isinstance(case, dict) or set(case) != CASE_KEYS:
            raise ValueError("case has unexpected or missing fields")
        case_id = case["case_id"]
        if not isinstance(case_id, str) or not case_id or not case_id.isidentifier():
            raise ValueError("case_id must be a nonempty identifier")
        if case_id in case_ids:
            raise ValueError(f"duplicate case_id: {case_id}")
        case_ids.add(case_id)
        if not isinstance(case["family"], str) or not case["family"]:
            raise ValueError(f"{case_id}: family must be a nonempty string")
        families.add(case["family"])
        if not isinstance(case["function_name"], str) or not case["function_name"].isidentifier():
            raise ValueError(f"{case_id}: function_name must be an identifier")
        parameters = case["parameters"]
        if (
            not isinstance(parameters, list)
            or not parameters
            or any(not isinstance(name, str) or not name.isidentifier() or name.startswith("__") for name in parameters)
            or len(parameters) != len(set(parameters))
        ):
            raise ValueError(f"{case_id}: parameters must be unique ordinary identifiers")
        for text_field in ("requirement", "flaw_rationale"):
            if not isinstance(case[text_field], str) or not case[text_field].strip():
                raise ValueError(f"{case_id}: {text_field} must be nonempty")

        expected_case_paths = [
            f"cases/{case_id}_correct.py",
            f"cases/{case_id}_flawed.py",
        ]
        case_paths = [case["correct_path"], case["flawed_path"]]
        if case_paths != expected_case_paths:
            raise ValueError(f"{case_id}: fixture paths do not match the explicit case ID")
        expected_paths.extend(expected_case_paths)

        if not isinstance(case["visible_examples"], list) or len(case["visible_examples"]) < 2:
            raise ValueError(f"{case_id}: at least two visible examples are required")
        if not isinstance(case["contract_checks"], list) or not case["contract_checks"]:
            raise ValueError(f"{case_id}: at least one contract check is required")
        check_ids: set[str] = set()
        for collection, required_keys in (
            (case["visible_examples"], VISIBLE_CHECK_KEYS),
            (case["contract_checks"], CONTRACT_CHECK_KEYS),
        ):
            for check in collection:
                if not isinstance(check, dict) or set(check) != required_keys:
                    raise ValueError(f"{case_id}: check has unexpected or missing fields")
                check_id = check["check_id"]
                if not isinstance(check_id, str) or not check_id.isidentifier() or check_id in check_ids:
                    raise ValueError(f"{case_id}: check IDs must be unique identifiers")
                check_ids.add(check_id)
                if not isinstance(check["input"], list):
                    raise ValueError(f"{case_id}/{check_id}: input must be an argument list")
        if any(type(check["witness"]) is not bool for check in case["contract_checks"]):
            raise ValueError(f"{case_id}: contract witness flags must be booleans")
        if not any(check["witness"] for check in case["contract_checks"]):
            raise ValueError(f"{case_id}: at least one intentional witness is required")

    if len(families) < 3:
        raise ValueError("inventory must cover at least three utility families")
    if inventory["fixture_paths"] != expected_paths or len(expected_paths) != EXPECTED_FIXTURE_COUNT:
        raise ValueError("explicit fixture_paths must list the exact twelve case files in case order")

    actual_paths = sorted(
        path.relative_to(FOLLOWUP_DIR).as_posix()
        for path in CASES_DIR.rglob("*.py")
    )
    if len(actual_paths) != EXPECTED_FIXTURE_COUNT or set(actual_paths) != set(expected_paths):
        raise ValueError("checked-in fixture directory does not contain the exact twelve inventoried files")


def _normalized_source(relative_path: str) -> tuple[str, str]:
    pure_path = PurePosixPath(relative_path)
    if pure_path.parts[0:1] != ("cases",) or len(pure_path.parts) != 2 or pure_path.suffix != ".py":
        raise ValueError(f"fixture path is outside the fixed cases directory: {relative_path}")
    source_path = CASES_DIR / pure_path.name
    resolved_path = source_path.resolve()
    if not resolved_path.is_relative_to(CASES_DIR.resolve()):
        raise ValueError(f"fixture path resolves outside the fixed cases directory: {relative_path}")
    source = source_path.read_bytes().decode("utf-8")
    normalized_source = source.replace("\r\n", "\n").replace("\r", "\n")
    digest = hashlib.sha256(normalized_source.encode("utf-8")).hexdigest()
    return normalized_source, digest


def _validate_source(source: str, case: dict[str, Any], relative_path: str) -> ast.Module:
    tree = ast.parse(source, filename=relative_path, mode="exec")
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
        raise ValueError(f"{case['case_id']}: expected exactly one top-level synchronous function")
    function = tree.body[0]
    if (
        function.name != case["function_name"]
        or function.decorator_list
        or function.returns is not None
        or len(function.body) != 1
        or not isinstance(function.body[0], ast.Return)
    ):
        raise ValueError(f"{case['case_id']}: unexpected function declaration or body")
    arguments = function.args
    if (
        [argument.arg for argument in arguments.args] != case["parameters"]
        or arguments.posonlyargs
        or arguments.kwonlyargs
        or arguments.vararg is not None
        or arguments.kwarg is not None
        or arguments.defaults
        or arguments.kw_defaults
        or any(argument.annotation is not None for argument in arguments.args)
    ):
        raise ValueError(f"{case['case_id']}: function parameters differ from the inventory")

    local_names = set(case["parameters"])
    local_names.update(
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
    )
    allowed_names = local_names | set(SAFE_BUILTINS)
    for node in ast.walk(tree):
        if type(node) not in ALLOWED_AST_NODES:
            raise ValueError(f"{case['case_id']}: disallowed syntax {type(node).__name__}")
        if isinstance(node, ast.Name) and (node.id.startswith("__") or node.id not in allowed_names):
            raise ValueError(f"{case['case_id']}: disallowed or unresolved name {node.id}")
        if isinstance(node, ast.Attribute) and (
            node.attr.startswith("_") or node.attr not in PURE_METHODS
        ):
            raise ValueError(f"{case['case_id']}: disallowed attribute {node.attr}")
        if isinstance(node, ast.Call):
            if node.keywords:
                raise ValueError(f"{case['case_id']}: keyword calls are not allowed")
            if isinstance(node.func, ast.Name) and node.func.id not in SAFE_BUILTINS:
                raise ValueError(f"{case['case_id']}: disallowed call {node.func.id}")
            if isinstance(node.func, ast.Attribute) and node.func.attr not in PURE_METHODS:
                raise ValueError(f"{case['case_id']}: disallowed method call {node.func.attr}")
            if not isinstance(node.func, (ast.Name, ast.Attribute)):
                raise ValueError(f"{case['case_id']}: dynamic calls are not allowed")
    return tree


def _matches_expected(actual: Any, expected: Any) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(actual, list):
        return len(actual) == len(expected) and all(
            _matches_expected(actual_item, expected_item)
            for actual_item, expected_item in zip(actual, expected)
        )
    if isinstance(actual, dict):
        return actual.keys() == expected.keys() and all(
            _matches_expected(actual[key], expected[key]) for key in expected
        )
    return actual == expected


def _checks_for_case(case: dict[str, Any]) -> list[dict[str, Any]]:
    checks = [
        {"kind": "visible", **check}
        for check in case["visible_examples"]
    ]
    checks.extend(
        {"kind": "contract", **check}
        for check in case["contract_checks"]
    )
    return checks


def _run_check(function: Any, case_id: str, check: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "check_id": check["check_id"],
        "kind": check["kind"],
        "check_sha256": _canonical_sha256({"case_id": case_id, **check}),
        "input": check["input"],
        "expected": check["expected"],
        "witness": check.get("witness", False),
    }
    try:
        actual = function(*check["input"])
        actual_json = json.loads(json.dumps(actual, ensure_ascii=False, allow_nan=False))
        matches = _matches_expected(actual, check["expected"])
    except Exception as error:
        result.update({
            "actual": None,
            "status": "RUNTIME_ERROR",
            "error_type": type(error).__name__,
            "error_message": str(error),
        })
        return result
    result["actual"] = actual_json
    result["status"] = "PASS" if matches else "MISMATCH"
    return result


def _evaluate_variant(case: dict[str, Any], role: str, checks: list[dict[str, Any]]) -> dict[str, Any]:
    relative_path = case[f"{role}_path"]
    source, source_sha256 = _normalized_source(relative_path)
    tree = _validate_source(source, case, relative_path)
    compiled = compile(tree, relative_path, "exec", dont_inherit=True)
    results = []
    for check in checks:
        namespace: dict[str, Any] = {"__builtins__": SAFE_BUILTINS}
        exec(compiled, namespace, namespace)
        results.append(_run_check(namespace[case["function_name"]], case["case_id"], check))

    visible_checks = [result for result in results if result["kind"] == "visible"]
    contract_checks = [result for result in results if result["kind"] == "contract"]
    visible_pass = all(result["status"] == "PASS" for result in visible_checks)
    contract_pass = all(result["status"] == "PASS" for result in contract_checks)
    runtime_errors = any(result["status"] == "RUNTIME_ERROR" for result in results)
    witness_mismatch = any(
        result["witness"] and result["status"] == "MISMATCH"
        for result in contract_checks
    )
    if role == "correct":
        status = "PASS" if visible_pass and contract_pass and not runtime_errors else "FAIL"
    else:
        status = (
            "PASS_VISIBLE_WITH_CONTRACT_WITNESS"
            if visible_pass and witness_mismatch and not runtime_errors
            else "FAIL"
        )
    return {
        "source_path": relative_path,
        "source_sha256": source_sha256,
        "status": status,
        "visible_checks_pass": visible_pass,
        "contract_checks_pass": contract_pass,
        "intentional_witness_mismatch": witness_mismatch,
        "runtime_error": runtime_errors,
        "checks": results,
    }


def _evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    checks = _checks_for_case(case)
    checks_sha256 = _canonical_sha256({"case_id": case["case_id"], "checks": checks})
    correct = _evaluate_variant(case, "correct", checks)
    flawed = _evaluate_variant(case, "flawed", checks)
    visible_pass = correct["visible_checks_pass"] and flawed["visible_checks_pass"]
    correct_contract_pass = correct["contract_checks_pass"]
    witness_present = flawed["intentional_witness_mismatch"]
    no_runtime_errors = not correct["runtime_error"] and not flawed["runtime_error"]
    criteria = {
        "both_variants_pass_visible_examples": visible_pass,
        "correct_variant_passes_contract_checks": correct_contract_pass,
        "flawed_variant_mismatches_intentional_witness": witness_present,
        "neither_variant_has_runtime_errors": no_runtime_errors,
    }
    failed_criteria = [criterion for criterion, passed in criteria.items() if not passed]
    return {
        "case_id": case["case_id"],
        "family": case["family"],
        "checks_sha256": checks_sha256,
        "criteria": criteria,
        "failed_criteria": failed_criteria,
        "eligible": not failed_criteria,
        "variants": {"correct": correct, "flawed": flawed},
    }


def run_screen() -> dict[str, Any]:
    inventory = load_inventory()
    validate_inventory(inventory)
    cases = [_evaluate_case(case) for case in inventory["cases"]]
    eligible_count = sum(case["eligible"] for case in cases)
    if eligible_count == EXPECTED_CASE_COUNT:
        status = "TARGET_MET"
    elif eligible_count >= 5:
        status = "FEASIBLE"
    else:
        status = "BELOW_FEASIBILITY_FLOOR"
    return {
        "schema_version": 1,
        "execution_status": "COMPLETE",
        "scope": "development_only",
        "criterion": (
            "Both variants match every visible example; the correct variant matches every contract check; "
            "the flawed variant mismatches at least one marked contract witness; neither variant raises."
        ),
        "identity_rules": {
            "source_sha256": "SHA-256 of UTF-8 source after CRLF and CR line endings are normalized to LF; the same normalized text is parsed and compiled.",
            "check_sha256": "SHA-256 of canonical UTF-8 JSON for the case ID and check fields, with sorted keys and compact separators.",
            "inventory_sha256": _canonical_sha256(inventory),
        },
        "score": {
            "case_count": len(cases),
            "eligible_pair_count": eligible_count,
            "ineligible_case_ids": [case["case_id"] for case in cases if not case["eligible"]],
            "feasibility_floor_met": eligible_count >= 5,
            "six_pair_target_met": eligible_count == EXPECTED_CASE_COUNT,
            "status": status,
        },
        "cases": cases,
    }


def _validate_output_path(output_path: Path) -> None:
    if RESULTS_DIR.is_symlink() or output_path.is_symlink():
        raise ValueError("output path and results directory cannot be symlinks")
    if output_path.suffix.lower() != ".json" or output_path.resolve() != SCREEN_SUMMARY_PATH.resolve():
        raise ValueError("output must be the canonical docs/followup/results/screen-summary.json file")
    if output_path.parent.resolve() != RESULTS_DIR.resolve():
        raise ValueError("output must be a direct child of the fixed results directory")


def _write_summary(output_path: Path, summary: dict[str, Any]) -> None:
    _validate_output_path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(summary, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="path for the deterministic JSON screen summary")
    arguments = parser.parse_args(argv)
    output_path = Path(arguments.output)
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    try:
        _validate_output_path(output_path)
        summary = run_screen()
        _write_summary(output_path, summary)
    except (OSError, UnicodeError, ValueError) as error:
        print(f"screen failed: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    score = summary["score"]
    print(f"screen_status={score['status']}; eligible_pairs={score['eligible_pair_count']}/{score['case_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
