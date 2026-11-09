"""Receipt-only descriptive reducer with explicit missingness accounting."""

from __future__ import annotations

import hashlib
import json
import math
import random
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from . import evidence
from .data import ROOT, load_cases, load_protocol
from .oracle_checks import load_oracle
from .prompt import COMMON_PROMPT, build_prompt


VALID_VERDICTS = {"PASS", "FAIL", "INDETERMINATE"}
TERMINAL_STATUSES = {"valid", "protocol_invalid", "invalid_output", "operational_unknown"}
WILSON_Z = 1.959963984540054
REPO_ROOT = ROOT.parent
PUBLIC_SCOPE = "public_projection_replay"
PRIVATE_SCOPE = "private_raw_verified"


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True, init=False)
class VerifiedEvidenceBundle:
    """Evidence admitted by the public projection or private raw verifier."""

    verification_scope: str
    freeze_sha256: str
    _freeze_bytes: bytes
    _reservations_bytes: bytes
    _admission_context_bytes: bytes
    _receipts_bytes: bytes
    _canary_reservations_bytes: bytes
    _canary_ledger_bytes: bytes
    _history_bytes: bytes
    history_sha256: str | None

    def __init__(
        self,
        *,
        verification_scope: str,
        freeze_sha256: str,
        freeze: dict[str, Any],
        reservations: list[dict[str, Any]],
        admission_context: dict[str, Any],
        receipts: list[dict[str, Any]],
        canary_reservations: Any,
        canary_ledger: list[dict[str, Any]],
        history: Any,
        history_sha256: str | None,
        _token: object,
    ) -> None:
        if _token is not _VERIFIED_BUNDLE_TOKEN:
            raise TypeError("VerifiedEvidenceBundle must come from load_verified_bundle")
        object.__setattr__(self, "verification_scope", verification_scope)
        object.__setattr__(self, "freeze_sha256", freeze_sha256)
        object.__setattr__(self, "_freeze_bytes", _canonical_json(freeze))
        object.__setattr__(self, "_reservations_bytes", _canonical_json(reservations))
        object.__setattr__(self, "_admission_context_bytes", _canonical_json(admission_context))
        object.__setattr__(self, "_receipts_bytes", _canonical_json(receipts))
        object.__setattr__(self, "_canary_reservations_bytes", _canonical_json(canary_reservations))
        object.__setattr__(self, "_canary_ledger_bytes", _canonical_json(canary_ledger))
        object.__setattr__(self, "_history_bytes", _canonical_json(history))
        object.__setattr__(self, "history_sha256", history_sha256)

    @property
    def freeze(self) -> dict[str, Any]:
        return json.loads(self._freeze_bytes)

    @property
    def reservations(self) -> list[dict[str, Any]]:
        return json.loads(self._reservations_bytes)

    @property
    def admission_context(self) -> dict[str, Any]:
        return json.loads(self._admission_context_bytes)

    @property
    def receipts(self) -> list[dict[str, Any]]:
        return json.loads(self._receipts_bytes)

    @property
    def canary_reservations(self) -> Any:
        return json.loads(self._canary_reservations_bytes)

    @property
    def canary_ledger(self) -> list[dict[str, Any]]:
        return json.loads(self._canary_ledger_bytes)

    @property
    def history(self) -> Any:
        return json.loads(self._history_bytes)


_VERIFIED_BUNDLE_TOKEN = object()


@dataclass(frozen=True)
class BlockedDiagnostic:
    code: str


def _ordered_schedule() -> list[dict[str, str]]:
    protocol = load_protocol()
    schedule = []
    for split in ("development", "holdout"):
        for case in load_cases(split):
            conditions = list(protocol["conditions"])
            random.Random(protocol["order_seed"] ^ int(case["case_id"][1:])).shuffle(conditions)
            for condition in conditions:
                prompt = build_prompt(case, condition)
                schedule.append({
                    "split": split,
                    "case_id": case["case_id"],
                    "condition": condition,
                    "prompt_sha256": _sha256(prompt.encode("utf-8")),
                    "code_sha256": _sha256(case["code"].encode("utf-8")),
                    "task_sha256": _sha256(case["task"].encode("utf-8")),
                    "criteria_sha256": _sha256(_canonical_json(case["criteria"])),
                    "common_prompt_sha256": _sha256(COMMON_PROMPT.encode("utf-8")),
                })
    return schedule


def _replay_event_stream(stdout: str, returncode: int | None, timed_out: bool = False) -> Any:
    from .codex_cli import parse_event_stream

    return parse_event_stream(stdout, returncode, timed_out)


def _replay_projection(projection: bytes, expected_model: str) -> Any:
    from .ollama import parse_projection

    return parse_projection(projection, expected_model)


def _legacy_protocol() -> dict[str, Any]:
    return evidence.read_json(REPO_ROOT / "docs" / "protocols" / "codex-v1.json")


def _check_current_scientific_binding(freeze: dict[str, Any], freeze_sha256: str) -> None:
    scientific_files = evidence.scientific_closure(REPO_ROOT)
    protocol = _legacy_protocol() if freeze.get("schema_version") == 1 else load_protocol()
    if freeze.get("scientific_files") != scientific_files:
        raise evidence.EvidenceError("SCIENTIFIC_FILES")
    if freeze.get("scientific_sha256") != evidence.freeze_sha256(scientific_files):
        raise evidence.EvidenceError("SCIENTIFIC_DIGEST")
    if freeze.get("protocol") != protocol:
        raise evidence.EvidenceError("PROTOCOL_MISMATCH")
    if freeze.get("schedule") != _ordered_schedule():
        raise evidence.EvidenceError("SCHEDULE_MISMATCH")
    if evidence.freeze_sha256(freeze) != freeze_sha256:
        raise evidence.EvidenceError("FREEZE_DIGEST")


def _blocked(error: Exception | str) -> BlockedDiagnostic:
    code = error if isinstance(error, str) else error.args[0] if error.args else "BUNDLE_VERIFICATION_FAILED"
    if not isinstance(code, str) or re.fullmatch(r"[A-Z0-9_]{1,64}", code) is None:
        code = "BUNDLE_VERIFICATION_FAILED"
    return BlockedDiagnostic(code)


def load_verified_bundle(
    root: Path,
    *,
    scope: str,
    manifest_sha256: str | None = None,
) -> VerifiedEvidenceBundle | BlockedDiagnostic:
    try:
        if scope == PUBLIC_SCOPE:
            if manifest_sha256 is None:
                raise evidence.EvidenceError("MANIFEST_DIGEST")
            manifest = evidence.read_json(Path(root) / "manifest.json")
            if isinstance(manifest, dict) and manifest.get("schema_version") == 2:
                if manifest.get("provider") != "ollama_local":
                    raise evidence.EvidenceError("UNSUPPORTED_PUBLIC_PROVIDER")
                verified = evidence.verify_v2_public_bundle(root, manifest_sha256, _replay_projection)
            elif isinstance(manifest, dict) and manifest.get("schema_version") == 1:
                verified = evidence.verify_public_bundle(root, manifest_sha256, replay=_replay_event_stream)
            else:
                raise evidence.EvidenceError("UNSUPPORTED_PUBLIC_SCHEMA")
        elif scope == PRIVATE_SCOPE:
            if manifest_sha256 is not None:
                raise evidence.EvidenceError("UNEXPECTED_MANIFEST_DIGEST")
            from .runner import load_private_bundle

            verified = load_private_bundle(Path(root))
        else:
            raise evidence.EvidenceError("UNSUPPORTED_VERIFICATION_SCOPE")

        if not isinstance(verified, dict) or verified.get("verification_scope") != scope:
            raise evidence.EvidenceError("VERIFICATION_SCOPE_MISMATCH")
        freeze = verified.get("freeze")
        freeze_sha256 = verified.get("freeze_sha256")
        reservations = verified.get("reservations")
        admission_context = verified.get("admission_context", {})
        receipts = verified.get("receipts")
        canary_reservations = verified.get("canary_reservations", [])
        canary_ledger = verified.get("canary_ledger", [])
        history = verified.get("history")
        history_sha256 = verified.get("history_sha256")
        if history_sha256 is None and isinstance(freeze, dict):
            history_sha256 = freeze.get("history_sha256")
        if not isinstance(freeze, dict) or not isinstance(freeze_sha256, str):
            raise evidence.EvidenceError("VERIFIED_BUNDLE_SCHEMA")
        valid_canary_reservations = type(canary_reservations) is int or isinstance(canary_reservations, list)
        if (not isinstance(reservations, list) or not isinstance(receipts, list) or not isinstance(admission_context, dict) or
                not valid_canary_reservations or not isinstance(canary_ledger, list)):
            raise evidence.EvidenceError("VERIFIED_BUNDLE_SCHEMA")
        _check_current_scientific_binding(freeze, freeze_sha256)
        if freeze.get("schema_version") == 2:
            evidence.verify_v2_inventory(freeze, reservations, receipts, freeze_sha256)
        else:
            evidence.verify_inventory(freeze, reservations, receipts, freeze_sha256)
        return VerifiedEvidenceBundle(
            verification_scope=scope,
            freeze_sha256=freeze_sha256,
            freeze=freeze,
            reservations=reservations,
            admission_context=admission_context,
            receipts=receipts,
            canary_reservations=canary_reservations,
            canary_ledger=canary_ledger,
            history=history,
            history_sha256=history_sha256,
            _token=_VERIFIED_BUNDLE_TOKEN,
        )
    except Exception as error:
        return _blocked(error)


def wilson_interval(successes: int, total: int) -> list[float]:
    if total < 0 or successes < 0 or successes > total:
        raise ValueError("invalid binomial counts")
    if total == 0:
        return [0.0, 1.0]
    proportion = successes / total
    z_squared = WILSON_Z * WILSON_Z
    denominator = 1 + z_squared / total
    center = (proportion + z_squared / (2 * total)) / denominator
    margin = WILSON_Z * math.sqrt(proportion * (1 - proportion) / total + z_squared / (4 * total * total)) / denominator
    return [max(0.0, center - margin), min(1.0, center + margin)]


def _status_and_verdict(receipt: dict[str, Any] | None) -> tuple[str, str | None]:
    if receipt is None:
        return "operational_unknown", None
    status = receipt.get("status")
    if status not in TERMINAL_STATUSES:
        return "protocol_invalid", None
    if status != "valid":
        return status, None
    verdict = receipt.get("verdict")
    if verdict not in VALID_VERDICTS:
        return "invalid_output", None
    return "valid", verdict


def _receipt_matches_cell(receipt: dict[str, Any], case: dict[str, Any], condition: str) -> bool:
    prompt = build_prompt(case, condition)
    expected_inputs = {
        "code": _sha256(case["code"].encode("utf-8")),
        "task": _sha256(case["task"].encode("utf-8")),
        "criteria": _sha256(_canonical_json(case["criteria"])),
        "common_prompt": _sha256(COMMON_PROMPT.encode("utf-8")),
        "prompt": _sha256(prompt.encode("utf-8")),
    }
    try:
        timestamp = datetime.fromisoformat(receipt["timestamp_utc"].replace("Z", "+00:00"))
    except (KeyError, AttributeError, ValueError):
        return False
    protocol = load_protocol()
    if type(receipt.get("schema_version")) is int and receipt["schema_version"] == 2:
        transport = receipt.get("transport")
        runtime = transport.get("runtime_identity") if isinstance(transport, dict) else None
        observed = runtime.get("observed") if isinstance(runtime, dict) else None
        expected_model = protocol["model"]["requested_alias"]
        return (
            timestamp.utcoffset() is not None
            and receipt.get("kind") == "study"
            and receipt.get("provider") == "ollama_local"
            and isinstance(receipt.get("scientific_sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", receipt["scientific_sha256"]) is not None
            and isinstance(transport.get("runtime_identity_sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", transport["runtime_identity_sha256"]) is not None
            and isinstance(observed, dict)
            and observed.get("model") == expected_model
            and receipt.get("reported_model") == expected_model
            and type(receipt.get("terminal_exit")) is int
            and receipt["terminal_exit"] == 0
            and receipt.get("timed_out") is False
            and receipt.get("cleanup_proven") is True
            and receipt.get("forced_cleanup") is False
            and type(receipt.get("active_processes_final")) is int
            and receipt["active_processes_final"] == 0
            and receipt.get("judge_directory_cleaned") is True
            and receipt.get("native_failed_step") is None
            and receipt.get("marker_echo") is False
            and isinstance(receipt.get("reason"), str)
            and 0 < len(receipt["reason"]) <= 300
            and receipt.get("input_sha256") == expected_inputs
            and not ({"stderr", "thread_id", "account_id", "cwd", "working_directory"} & receipt.keys())
        )

    protocol = _legacy_protocol()
    cli = receipt.get("cli")
    return (
        timestamp.utcoffset() is not None
        and receipt.get("requested_model") == protocol["model"]["requested_alias"]
        and receipt.get("reasoning_effort") == protocol["model"]["reasoning_effort"]
        and isinstance(receipt.get("scientific_sha256"), str)
        and re.fullmatch(r"[0-9a-f]{64}", receipt["scientific_sha256"]) is not None
        and isinstance(cli, dict)
        and isinstance(cli.get("version"), str)
        and bool(cli["version"])
        and cli.get("version_check_passed") is True
        and isinstance(cli.get("binary_sha256"), str)
        and re.fullmatch(r"[0-9a-f]{64}", cli["binary_sha256"]) is not None
        and isinstance(cli.get("configuration_sha256"), str)
        and re.fullmatch(r"[0-9a-f]{64}", cli["configuration_sha256"]) is not None
        and type(receipt.get("terminal_exit")) is int
        and receipt["terminal_exit"] == 0
        and receipt.get("timed_out") is False
        and receipt.get("cleanup_proven") is True
        and receipt.get("forced_cleanup") is False
        and type(receipt.get("active_processes_final")) is int
        and receipt["active_processes_final"] == 0
        and receipt.get("judge_directory_cleaned") is True
        and isinstance(receipt.get("reason"), str)
        and 0 < len(receipt["reason"]) <= 300
        and receipt.get("input_sha256") == expected_inputs
        and not ({"stderr", "thread_id", "account_id", "cwd", "working_directory"} & receipt.keys())
    )


def reconcile(split: str, receipts: list[dict[str, Any]]) -> dict[str, Any]:
    cases = load_cases(split)
    oracle = load_oracle()
    conditions = load_protocol()["conditions"]
    expected = {(case["case_id"], condition) for case in cases for condition in conditions}
    by_cell: dict[tuple[str, str], dict[str, Any]] = {}
    duplicate_cells: set[tuple[str, str]] = set()
    for receipt in receipts:
        slot_id = receipt.get("slot_id")
        if not isinstance(slot_id, str):
            continue
        if receipt.get("kind") not in {None, "study"}:
            continue
        parts = slot_id.split(":")
        if len(parts) != 4 or parts[0] != "study" or parts[1] != split:
            continue
        cell = (parts[2], parts[3])
        if cell not in expected:
            continue
        if cell in by_cell:
            duplicate_cells.add(cell)
        else:
            by_cell[cell] = receipt

    cells = []
    case_by_id = {case["case_id"]: case for case in cases}
    for case in cases:
        case_id = case["case_id"]
        truth = oracle[case_id]
        for condition in conditions:
            receipt = by_cell.get((case_id, condition))
            status, verdict = _status_and_verdict(receipt)
            if status == "valid" and receipt is not None and not _receipt_matches_cell(receipt, case_by_id[case_id], condition):
                status, verdict = "protocol_invalid", None
            if (case_id, condition) in duplicate_cells:
                status, verdict = "protocol_invalid", None
            cells.append({
                "case_id": case_id,
                "family": truth["family"],
                "label": truth["label"],
                "condition": condition,
                "status": status,
                "verdict": verdict,
            })
    return {"split": split, "conditions": conditions, "cells": cells, "planned_cells": len(expected)}


def _metric_value(label: str, verdict: str | None, metric: str) -> int | None:
    if verdict is None:
        return None
    if metric == "false_pass":
        return int(label == "defective" and verdict == "PASS")
    if metric == "correct_nonpass":
        return int(label == "correct" and verdict in {"FAIL", "INDETERMINATE"})
    if metric == "strict_false_reject":
        return int(label == "correct" and verdict == "FAIL")
    if metric == "abstention":
        return int(verdict == "INDETERMINATE")
    raise ValueError(f"unknown metric: {metric}")


def _rate_summary(cells: list[dict[str, Any]], label: str, condition: str, metric: str) -> dict[str, Any]:
    selected = [cell for cell in cells if cell["label"] == label and cell["condition"] == condition]
    valid = [cell for cell in selected if cell["status"] == "valid"]
    successes = sum(_metric_value(label, cell["verdict"], metric) or 0 for cell in valid)
    planned = len(selected)
    valid_count = len(valid)
    missing = planned - valid_count
    return {
        "numerator": successes,
        "valid_denominator": valid_count,
        "planned_denominator": planned,
        "wilson_95": wilson_interval(successes, valid_count),
        "missingness_bounds": [successes / planned if planned else 0.0,
                               (successes + missing) / planned if planned else 1.0],
    }


def _bootstrap_interval(
    differences_by_family: dict[str, list[int]],
    resamples: int,
    seed: int,
) -> list[float] | None:
    groups = {family: values for family, values in differences_by_family.items() if values}
    total = sum(len(values) for values in groups.values())
    if not total:
        return None
    rng = random.Random(seed)
    estimates = []
    for _ in range(resamples):
        sampled = []
        for family in sorted(groups):
            values = groups[family]
            sampled.extend(rng.choice(values) for _ in range(len(values)))
        estimates.append(sum(sampled) / len(sampled))
    estimates.sort()
    lower_index = int(0.025 * (resamples - 1))
    upper_index = int(0.975 * (resamples - 1))
    return [estimates[lower_index], estimates[upper_index]]


def paired_contrast(
    cells: list[dict[str, Any]],
    label: str,
    left_condition: str,
    right_condition: str,
    metric: str,
    planned_denominator: int,
    resamples: int = 10000,
    seed: int = 20261109,
) -> dict[str, Any]:
    by_case_condition = {(cell["case_id"], cell["condition"]): cell for cell in cells}
    relevant = [cell for cell in cells if cell["label"] == label]
    case_families = {cell["case_id"]: cell["family"] for cell in relevant}
    case_ids = sorted(case_families)
    differences_by_family: dict[str, list[int]] = {}
    for case_id in case_ids:
        left = by_case_condition[(case_id, left_condition)]
        right = by_case_condition[(case_id, right_condition)]
        if left["status"] != "valid" or right["status"] != "valid":
            continue
        left_value = _metric_value(label, left["verdict"], metric)
        right_value = _metric_value(label, right["verdict"], metric)
        if left_value is None or right_value is None:
            continue
        differences_by_family.setdefault(case_families[case_id], []).append(left_value - right_value)

    differences = [value for values in differences_by_family.values() for value in values]
    n_complete = len(differences)
    missing = planned_denominator - n_complete
    total_difference = sum(differences)
    positive = sum(value == 1 for value in differences)
    negative = sum(value == -1 for value in differences)
    zero = sum(value == 0 for value in differences)
    interval = _bootstrap_interval(differences_by_family, resamples, seed)
    return {
        "left_condition": left_condition,
        "right_condition": right_condition,
        "metric": metric,
        "raw_difference_count": total_difference,
        "risk_difference": total_difference / n_complete if n_complete else None,
        "complete_valid_pairs": n_complete,
        "planned_denominator": planned_denominator,
        "discordant_left_only": positive,
        "discordant_right_only": negative,
        "concordant": zero,
        "paired_bootstrap_95": interval,
        "zero_discordance_warning": bool(n_complete and positive == 0 and negative == 0),
        "family_pair_counts": {family: len(values) for family, values in sorted(differences_by_family.items())},
        "missingness_bounds_count": [total_difference - missing, total_difference + missing],
        "missing_pairs": missing,
    }


def _screen_at_least(delta: int, missing: int, threshold: int) -> str:
    lower = delta - missing
    upper = delta + missing
    if lower >= threshold:
        return "threshold_met"
    if upper < threshold:
        return "below_threshold_not_detected"
    return "inconclusive_missingness_can_reverse"


def framing_screen(contrast: dict[str, Any], threshold: int) -> dict[str, Any]:
    delta = contrast["raw_difference_count"]
    missing = contrast["missing_pairs"]
    return {
        "observed_extra_false_passes": delta,
        "missing_pairs": missing,
        "worst_case_count_bounds": contrast["missingness_bounds_count"],
        "threshold": threshold,
        "status": _screen_at_least(delta, missing, threshold),
    }


def mitigation_screen(
    defect_contrast: dict[str, Any],
    mitigation_nonpass_rate: dict[str, Any],
    added_nonpass_contrast: dict[str, Any],
    fewer_false_passes: int,
    max_correct_nonpass: int,
    max_added_nonpass: int,
) -> dict[str, Any]:
    reduction = -defect_contrast["raw_difference_count"]
    reduction_missing = defect_contrast["missing_pairs"]
    reduction_status = _screen_at_least(reduction, reduction_missing, fewer_false_passes)

    observed_nonpass = mitigation_nonpass_rate["numerator"]
    missing_controls = mitigation_nonpass_rate["planned_denominator"] - mitigation_nonpass_rate["valid_denominator"]
    nonpass_bounds = [observed_nonpass, observed_nonpass + missing_controls]
    if nonpass_bounds[1] <= max_correct_nonpass:
        nonpass_status = "threshold_met"
    elif nonpass_bounds[0] > max_correct_nonpass:
        nonpass_status = "threshold_failed"
    else:
        nonpass_status = "inconclusive_missingness_can_reverse"

    added_delta = added_nonpass_contrast["raw_difference_count"]
    added_missing = added_nonpass_contrast["missing_pairs"]
    added_bounds = added_nonpass_contrast["missingness_bounds_count"]
    if added_bounds[1] <= max_added_nonpass:
        added_status = "threshold_met"
    elif added_bounds[0] > max_added_nonpass:
        added_status = "threshold_failed"
    else:
        added_status = "inconclusive_missingness_can_reverse"

    statuses = [reduction_status, nonpass_status, added_status]
    if "threshold_failed" in statuses or "below_threshold_not_detected" in statuses:
        overall = "target_not_met"
    elif all(status == "threshold_met" for status in statuses):
        overall = "observed_target"
    else:
        overall = "inconclusive_missingness_can_reverse"
    return {
        "status": overall,
        "false_pass_reduction": {
            "observed_count": reduction,
            "missing_pairs": reduction_missing,
            "status": reduction_status,
        },
        "mitigation_correct_nonpass": {
            "observed_count": observed_nonpass,
            "planned_denominator": mitigation_nonpass_rate["planned_denominator"],
            "missing_controls": missing_controls,
            "worst_case_bounds": nonpass_bounds,
            "status": nonpass_status,
        },
        "added_correct_nonpass_vs_report_free": {
            "observed_count": added_delta,
            "missing_pairs": added_missing,
            "worst_case_bounds": added_bounds,
            "status": added_status,
        },
        "thresholds": {
            "fewer_false_passes": fewer_false_passes,
            "max_correct_nonpass": max_correct_nonpass,
            "max_added_correct_nonpass": max_added_nonpass,
        },
    }


def _analyze_receipts(split: str, receipts: list[dict[str, Any]]) -> dict[str, Any]:
    if split not in {"development", "holdout"}:
        raise ValueError("split must be development or holdout")
    reconciled = reconcile(split, receipts)
    cells = reconciled["cells"]
    protocol = load_protocol()
    conditions = protocol["conditions"]
    expected_labels = {cell["case_id"]: cell["label"] for cell in cells}
    defective_count = sum(label == "defective" for label in expected_labels.values())
    correct_count = sum(label == "correct" for label in expected_labels.values())

    condition_tables = {}
    status_counts = {}
    for condition in conditions:
        condition_cells = [cell for cell in cells if cell["condition"] == condition]
        statuses = Counter(cell["status"] for cell in condition_cells)
        verdicts = Counter(cell["verdict"] for cell in condition_cells if cell["status"] == "valid")
        status_counts[condition] = {status: statuses.get(status, 0) for status in sorted(TERMINAL_STATUSES)}
        condition_tables[condition] = {
            "status_counts": status_counts[condition],
            "verdict_counts": {verdict: verdicts.get(verdict, 0) for verdict in ("PASS", "FAIL", "INDETERMINATE")},
            "false_passes_on_defects": _rate_summary(cells, "defective", condition, "false_pass"),
            "strict_false_rejects_on_controls": _rate_summary(cells, "correct", condition, "strict_false_reject"),
            "abstentions_on_controls": _rate_summary(cells, "correct", condition, "abstention"),
            "correct_nonpasses": _rate_summary(cells, "correct", condition, "correct_nonpass"),
        }

    family_tables = {}
    for family in sorted({cell["family"] for cell in cells}):
        family_cells = [cell for cell in cells if cell["family"] == family]
        family_tables[family] = {}
        for condition in conditions:
            selected = [cell for cell in family_cells if cell["condition"] == condition]
            family_tables[family][condition] = {
                "cases": len(selected),
                "defective": sum(cell["label"] == "defective" for cell in selected),
                "correct": sum(cell["label"] == "correct" for cell in selected),
                "status_counts": dict(Counter(cell["status"] for cell in selected)),
                "false_passes": sum(cell["label"] == "defective" and cell["verdict"] == "PASS" and cell["status"] == "valid" for cell in selected),
                "strict_false_rejects": sum(cell["label"] == "correct" and cell["verdict"] == "FAIL" and cell["status"] == "valid" for cell in selected),
                "abstentions": sum(cell["verdict"] == "INDETERMINATE" and cell["status"] == "valid" for cell in selected),
            }

    framing = paired_contrast(
        cells, "defective", "persuasive", "neutral", "false_pass", defective_count,
        protocol["bootstrap"]["resamples"], protocol["bootstrap"]["seed"],
    )
    report_presence = paired_contrast(
        cells, "defective", "persuasive", "report_free", "false_pass", defective_count,
        protocol["bootstrap"]["resamples"], protocol["bootstrap"]["seed"],
    )
    mitigation_defects = paired_contrast(
        cells, "defective", "mitigation", "persuasive", "false_pass", defective_count,
        protocol["bootstrap"]["resamples"], protocol["bootstrap"]["seed"],
    )
    mitigation_controls = paired_contrast(
        cells, "correct", "mitigation", "report_free", "correct_nonpass", correct_count,
        protocol["bootstrap"]["resamples"], protocol["bootstrap"]["seed"],
    )
    mitigation = mitigation_screen(
        mitigation_defects,
        condition_tables["mitigation"]["correct_nonpasses"],
        mitigation_controls,
        protocol["thresholds"]["mitigation_fewer_false_passes"],
        protocol["thresholds"]["mitigation_max_correct_nonpass"],
        protocol["thresholds"]["mitigation_max_added_correct_nonpass"],
    )
    result = {
        "split": split,
        "planned_cells": reconciled["planned_cells"],
        "accounted_cells": len(cells),
        "valid_cells": sum(cell["status"] == "valid" for cell in cells),
        "condition_tables": condition_tables,
        "family_tables": family_tables,
        "paired_contrasts": {
            "persuasive_minus_neutral_false_pass": framing,
            "persuasive_minus_report_free_false_pass": report_presence,
            "mitigation_minus_persuasive_false_pass": mitigation_defects,
            "mitigation_minus_report_free_correct_nonpass": mitigation_controls,
        },
        "practical_screens": {
            "framing": framing_screen(framing, protocol["thresholds"]["framing_extra_false_passes"]),
            "mitigation": mitigation,
        },
        "cells": cells,
        "limitations": [
            "Intervals are descriptive case-level uncertainty conditional on these authored fixtures.",
            "A below-threshold screen is not evidence of no effect.",
            "The paired bootstrap conditions on complete valid pairs and preserves observed family composition.",
        ],
    }
    return result


def analyze(split: str, bundle: Any) -> dict[str, Any]:
    if split not in {"development", "holdout"}:
        raise ValueError("split must be development or holdout")
    if isinstance(bundle, BlockedDiagnostic):
        return {"status": "BLOCKED", "diagnostic": bundle.code}
    if not isinstance(bundle, VerifiedEvidenceBundle):
        return {"status": "BLOCKED", "diagnostic": "UNVERIFIED_INPUT"}
    result = _analyze_receipts(split, bundle.receipts)
    result["status"] = "PASS"
    result["verification_scope"] = bundle.verification_scope
    result["freeze_sha256"] = bundle.freeze_sha256
    return result
