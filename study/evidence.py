"""Portable, fail-closed evidence primitives for the frozen study.

The caller must reopen the expected freeze, admission and input files before
passing their contents here. Public replay verifies published commitments and
projections; it cannot independently verify unpublished raw capture bytes.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from .protocol import canonical_json


class EvidenceError(ValueError):
    """An evidence artifact is missing, malformed, or contradicts its binding."""


def _boundary(function):
    @wraps(function)
    def checked(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except EvidenceError:
            raise
        except (KeyError, TypeError, AttributeError, ValueError, OSError) as error:
            raise EvidenceError("MALFORMED_EVIDENCE") from error
    return checked


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def freeze_sha256(freeze: dict[str, Any]) -> str:
    return _digest(canonical_json(freeze))


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise EvidenceError(code)


def _sha(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _integer(value: Any) -> bool:
    return type(value) is int and value >= 0


def _public_cli(cli: Any) -> bool:
    return (isinstance(cli, dict) and set(cli) == {"version", "binary_sha256", "configuration_sha256", "version_check_passed"} and
            isinstance(cli["version"], str) and re.fullmatch(r"[A-Za-z0-9._+-]{1,120}", cli["version"]) is not None and
            _sha(cli["binary_sha256"]) and _sha(cli["configuration_sha256"]) and cli["version_check_passed"] is True)


def _json(data: bytes) -> Any:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in pairs:
            _require(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=unique)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EvidenceError("INVALID_JSON") from error


def read_json(path: Path) -> Any:
    try:
        return _json(Path(path).read_bytes())
    except OSError as error:
        raise EvidenceError("UNREADABLE_JSON") from error


def scientific_closure(repo_root: Path) -> dict[str, str]:
    root = Path(repo_root).resolve()
    study = root / "study"
    spec = root / "docs" / "SPEC.md"
    _require(study.is_dir() and spec.is_file(), "SCIENTIFIC_SOURCE_MISSING")
    files = [path for path in study.rglob("*") if path.is_file() and not any(
        part in {"__pycache__", ".pytest_cache", ".ruff_cache"} for part in path.parts
    ) and path.suffix not in {".pyc", ".pyo"}]
    files.append(spec)
    _require(all(not path.is_symlink() and path.resolve().is_relative_to(root) for path in files), "SCIENTIFIC_SYMLINK")
    try:
        return {path.relative_to(root).as_posix(): _digest(path.read_bytes()) for path in sorted(files)}
    except OSError as error:
        raise EvidenceError("SCIENTIFIC_SOURCE_UNREADABLE") from error


@_boundary
def verify_freeze(
    freeze: dict[str, Any], expected_sha256: str, *, scientific_files: dict[str, str],
    protocol: dict[str, Any], schedule: list[dict[str, Any]], cli: dict[str, Any],
    admission: dict[str, Any], admission_context: dict[str, Any],
    admission_receipt_paths: dict[str, Path], verify_admission_receipt: Callable[[str, dict[str, Any]], bool],
) -> str:
    """Join a reopened freeze to independently reopened expected artifacts."""
    keys = {"schema_version", "frozen_utc", "scientific_files", "scientific_sha256", "protocol", "schedule", "cli", "auth_route", "admission"}
    _require(isinstance(freeze, dict) and set(freeze) == keys and type(freeze["schema_version"]) is int and freeze["schema_version"] == 1, "FREEZE_SCHEMA")
    _require(_sha(expected_sha256) and freeze_sha256(freeze) == expected_sha256, "FREEZE_DIGEST")
    _require(datetime.fromisoformat(freeze["frozen_utc"].replace("Z", "+00:00")).utcoffset().total_seconds() == 0, "FREEZE_TIME")
    _require(freeze["scientific_files"] == scientific_files, "SCIENTIFIC_FILES")
    _require(all(isinstance(k, str) and _sha(v) for k, v in scientific_files.items()), "SCIENTIFIC_MAP")
    _require(freeze["scientific_sha256"] == freeze_sha256(scientific_files), "SCIENTIFIC_DIGEST")
    _require(freeze["protocol"] == protocol, "PROTOCOL_MISMATCH")
    _require(freeze["schedule"] == schedule, "SCHEDULE_MISMATCH")
    _require(freeze["cli"] == cli, "CLI_MISMATCH")
    _require(freeze["auth_route"] == "chatgpt_subscription", "AUTH_ROUTE")
    _require(freeze["admission"] == admission, "ADMISSION_MISMATCH")
    _require(isinstance(admission, dict) and admission.get("status") == "PASS", "ADMISSION_STATUS")
    _require(admission.get("scientific_sha256") == freeze["scientific_sha256"], "ADMISSION_SCIENCE")
    _require(admission.get("cli") == cli, "ADMISSION_CLI")
    _require(admission_context.get("requested_model") == protocol.get("model", {}).get("requested_alias") and
             admission_context.get("reasoning_effort") == protocol.get("model", {}).get("reasoning_effort"), "ADMISSION_MODEL")
    verify_admission(admission, admission_context, admission_receipt_paths, verify_admission_receipt)
    _require(isinstance(schedule, list), "SCHEDULE_SCHEMA")
    slots = [_slot(cell) for cell in schedule]
    _require(len(slots) == len(set(slots)), "DUPLICATE_SCHEDULE_SLOT")
    budget = protocol.get("turn_budget", {})
    _require(_integer(budget.get("study")) and len(schedule) == budget["study"], "SCHEDULE_BUDGET")
    return expected_sha256


def _slot(cell: dict[str, Any]) -> str:
    _require(isinstance(cell, dict) and all(isinstance(cell.get(k), str) and cell[k] for k in ("split", "case_id", "condition")), "SCHEDULE_CELL")
    return f"study:{cell['split']}:{cell['case_id']}:{cell['condition']}"


@_boundary
def verify_admission(
    admission: dict[str, Any], context: dict[str, Any], receipt_paths: dict[str, Path],
    verify_receipt: Callable[[str, dict[str, Any]], bool],
) -> None:
    """Reopen both canary receipts; callback must independently verify raw custody.

    Context is fixed before dispatch and includes exact prompt/marker commitments.
    This is deliberately separate from freeze verification to avoid a circular gate.
    """
    _require(set(context) == {"scientific_sha256", "cli", "requested_model", "reasoning_effort", "predicates"}, "ADMISSION_CONTEXT")
    predicates = context["predicates"]
    _require(isinstance(predicates, dict) and set(predicates) == {"structured", "marker"}, "ADMISSION_PREDICATES")
    structured = predicates["structured"]
    marker = predicates["marker"]
    _require(isinstance(structured, dict) and set(structured) == {"prompt_sha256", "verdict", "reason"} and
             _sha(structured["prompt_sha256"]) and structured["verdict"] == "PASS" and
             structured["reason"] == "structured response available", "STRUCTURED_PREDICATE")
    _require(isinstance(marker, dict) and set(marker) == {"prompt_sha256", "marker_sha256", "verdict"} and
             _sha(marker["prompt_sha256"]) and _sha(marker["marker_sha256"]) and
             marker["verdict"] == "INDETERMINATE", "MARKER_PREDICATE")
    _require(isinstance(admission, dict) and set(admission) == {"schema_version", "status", "admitted_utc", "scientific_sha256", "cli", "context_sha256", "receipt_sha256"} and
             type(admission["schema_version"]) is int and admission["schema_version"] == 1 and admission["status"] == "PASS", "ADMISSION_SCHEMA")
    _require(datetime.fromisoformat(admission["admitted_utc"].replace("Z", "+00:00")).utcoffset().total_seconds() == 0, "ADMISSION_TIME")
    _require(admission["context_sha256"] == freeze_sha256(context) and admission["scientific_sha256"] == context["scientific_sha256"] and
             admission["cli"] == context["cli"], "ADMISSION_CONTEXT_MISMATCH")
    _require(isinstance(admission["receipt_sha256"], dict) and set(admission["receipt_sha256"]) == {"structured", "marker"} and
             set(receipt_paths) == {"structured", "marker"}, "ADMISSION_RECEIPTS")
    attempts = set()
    for name in ("structured", "marker"):
        try:
            data = Path(receipt_paths[name]).read_bytes()
        except OSError as error:
            raise EvidenceError("ADMISSION_RECEIPT_UNREADABLE") from error
        _require(_digest(data) == admission["receipt_sha256"][name], "ADMISSION_RECEIPT_DIGEST")
        receipt = _json(data)
        keys = {"attempt_id", "predicate", "context_sha256", "sidecar_sha256", "status", "verdict", "reason", "tool_event", "marker_echo",
                "cleanup_proven", "forced_cleanup", "active_processes_final", "judge_directory_cleaned"}
        _require(isinstance(receipt, dict) and set(receipt) == keys, "ADMISSION_RECEIPT_SCHEMA")
        _require(_sha(receipt["sidecar_sha256"]), "ADMISSION_SIDECAR_DIGEST")
        _require(isinstance(receipt["attempt_id"], str) and bool(receipt["attempt_id"]) and receipt["attempt_id"] not in attempts, "ADMISSION_ATTEMPT")
        attempts.add(receipt["attempt_id"])
        _require(receipt["predicate"] == name and receipt["context_sha256"] == admission["context_sha256"] and receipt["status"] == "valid" and
                 receipt["verdict"] == predicates[name]["verdict"] and isinstance(receipt["reason"], str) and bool(receipt["reason"].strip()), "ADMISSION_RESULT")
        if name == "structured":
            _require(receipt["reason"] == structured["reason"], "STRUCTURED_REASON")
        _require(receipt["tool_event"] is False and receipt["marker_echo"] is False and receipt["cleanup_proven"] is True and
                 receipt["forced_cleanup"] is False and type(receipt["active_processes_final"]) is int and
                 receipt["active_processes_final"] == 0 and receipt["judge_directory_cleaned"] is True, "ADMISSION_CUSTODY")
        _require(verify_receipt(name, receipt) is True, "ADMISSION_RAW_VERIFICATION")


RESERVATION_KEYS = {"schema_version", "attempt_id", "slot_id", "kind", "schedule_index", "reserved_utc", "freeze_sha256"}
RECEIPT_KEYS = RESERVATION_KEYS | {
    "scientific_sha256", "cli", "requested_model", "reasoning_effort", "input_sha256",
    "status", "verdict", "reason", "reported_model", "terminal_exit", "timed_out",
    "cleanup_proven", "forced_cleanup", "active_processes_final", "judge_directory_cleaned",
    "stdout_sha256", "stderr_sha256", "stdout_bytes", "stderr_bytes", "timestamp_utc", "sidecar_sha256",
}


def _replayed(result: Any) -> tuple[Any, Any, Any, Any]:
    if isinstance(result, dict):
        return tuple(result.get(key) for key in ("status", "verdict", "reason", "reported_model"))
    return tuple(getattr(result, key) for key in ("status", "verdict", "reason", "reported_model"))


def _validate_receipt(freeze: dict[str, Any], freeze_hash: str, reservation: dict[str, Any], receipt: dict[str, Any]) -> None:
    _require(isinstance(reservation, dict) and set(reservation) == RESERVATION_KEYS and type(reservation["schema_version"]) is int and reservation["schema_version"] == 1, "RESERVATION_SCHEMA")
    _require(isinstance(receipt, dict) and set(receipt) == RECEIPT_KEYS and type(receipt["schema_version"]) is int and receipt["schema_version"] == 1, "RECEIPT_SCHEMA")
    for key in RESERVATION_KEYS:
        _require(receipt[key] == reservation[key], "RESERVATION_JOIN")
    _require(reservation["freeze_sha256"] == freeze_hash, "RECEIPT_FREEZE")
    _require(reservation["kind"] == "study" and _integer(reservation["schedule_index"]) and
             reservation["schedule_index"] < len(freeze["schedule"]) and
             _slot(freeze["schedule"][reservation["schedule_index"]]) == reservation["slot_id"], "RESERVATION_SCHEDULE")
    try:
        reserved = datetime.fromisoformat(reservation["reserved_utc"].replace("Z", "+00:00"))
        _require(reserved.utcoffset() is not None, "NAIVE_RESERVATION")
    except (ValueError, TypeError, AttributeError) as error:
        raise EvidenceError("INVALID_RESERVATION_TIME") from error
    _require(isinstance(receipt["attempt_id"], str) and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", receipt["attempt_id"]) is not None, "ATTEMPT_ID")
    cells = [cell for cell in freeze["schedule"] if _slot(cell) == receipt["slot_id"]]
    _require(len(cells) == 1, "UNEXPECTED_SLOT")
    cell = cells[0]
    inputs = {key: cell[f"{key}_sha256"] for key in ("code", "task", "criteria", "common_prompt", "prompt")}
    _require(receipt["input_sha256"] == inputs and all(_sha(v) for v in inputs.values()), "INPUT_MISMATCH")
    _require(receipt["scientific_sha256"] == freeze["scientific_sha256"], "RECEIPT_SCIENCE")
    _require(receipt["cli"] == freeze["cli"], "RECEIPT_CLI")
    _require(receipt["requested_model"] == freeze["protocol"]["model"]["requested_alias"] and
             receipt["reasoning_effort"] == freeze["protocol"]["model"]["reasoning_effort"], "RECEIPT_MODEL")
    try:
        timestamp = datetime.fromisoformat(receipt["timestamp_utc"].replace("Z", "+00:00"))
        _require(timestamp.utcoffset() is not None, "NAIVE_TIMESTAMP")
    except (ValueError, TypeError, AttributeError) as error:
        raise EvidenceError("INVALID_TIMESTAMP") from error
    _require(receipt["status"] in {"valid", "invalid_output", "protocol_invalid", "operational_unknown"}, "RECEIPT_STATUS")
    _require(_sha(receipt["sidecar_sha256"]), "SIDECAR_DIGEST")
    for name in ("stdout", "stderr"):
        present = _sha(receipt[f"{name}_sha256"]) and _integer(receipt[f"{name}_bytes"])
        absent = receipt[f"{name}_sha256"] is None and receipt[f"{name}_bytes"] is None
        _require(present or (receipt["status"] != "valid" and absent), "CAPTURE_COMMITMENT")
    if receipt["status"] == "valid":
        _require(type(receipt["terminal_exit"]) is int and receipt["terminal_exit"] == 0 and receipt["timed_out"] is False and
                 receipt["cleanup_proven"] is True and receipt["forced_cleanup"] is False and
                 type(receipt["active_processes_final"]) is int and receipt["active_processes_final"] == 0 and
                 receipt["judge_directory_cleaned"] is True, "VALID_CUSTODY")
        _require(receipt["verdict"] in {"PASS", "FAIL", "INDETERMINATE"} and isinstance(receipt["reason"], str) and bool(receipt["reason"].strip()), "VALID_VERDICT")
    else:
        _require(receipt["verdict"] is None and receipt["reason"] is None, "FAILED_VERDICT")


@_boundary
def verify_private_receipt(
    freeze: dict[str, Any], freeze_hash: str, reservation: dict[str, Any], receipt: dict[str, Any],
    stdout_path: Path, stderr_path: Path, replay: Callable[..., Any],
) -> dict[str, Any]:
    """Reopen raw captures and compare production parser replay to receipt facts."""
    _validate_receipt(freeze, freeze_hash, reservation, receipt)
    stdout = bytearray()
    try:
        for name, path in (("stdout", stdout_path), ("stderr", stderr_path)):
            digest, count = hashlib.sha256(), 0
            with Path(path).open("rb") as stream:
                while chunk := stream.read(65536):
                    digest.update(chunk)
                    count += len(chunk)
                    if name == "stdout":
                        _require(count <= 8 * 1024 * 1024, "RAW_STDOUT_OVERSIZED")
                        stdout.extend(chunk)
            _require(digest.hexdigest() == receipt[f"{name}_sha256"] and count == receipt[f"{name}_bytes"], "RAW_CAPTURE_MISMATCH")
    except OSError as error:
        raise EvidenceError("RAW_CAPTURE_UNREADABLE") from error
    try:
        parsed = replay(bytes(stdout).decode("utf-8", errors="strict"), receipt["terminal_exit"], receipt["timed_out"])
    except (UnicodeError, ValueError, TypeError) as error:
        raise EvidenceError("RAW_REPLAY_FAILED") from error
    expected = tuple(receipt[key] for key in ("status", "verdict", "reason", "reported_model"))
    _require(_with_custody(parsed, receipt) == expected, "RAW_REPLAY_MISMATCH")
    return {"verification_scope": "private_raw_verified", "receipt": receipt}


def _with_custody(parsed: Any, receipt: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
    replayed = _replayed(parsed)
    if (receipt["terminal_exit"] != 0 or receipt["timed_out"] is not False or
            receipt["cleanup_proven"] is not True or receipt["forced_cleanup"] is not False or
            receipt["active_processes_final"] != 0 or receipt["judge_directory_cleaned"] is not True):
        return "operational_unknown", None, None, replayed[3]
    return replayed


@_boundary
def verify_inventory(freeze: dict[str, Any], reservations: list[dict[str, Any]], receipts: list[dict[str, Any]], freeze_hash: str) -> None:
    """Require a complete, unique ordered prefix of study reservations and receipts."""
    _require(isinstance(reservations, list) and isinstance(receipts, list), "INVENTORY_SCHEMA")
    _require(len(reservations) == len(receipts) <= len(freeze["schedule"]), "INVENTORY_COUNT")
    seen_attempts: set[str] = set()
    backend = None
    for index, (reservation, receipt) in enumerate(zip(reservations, receipts)):
        _validate_receipt(freeze, freeze_hash, reservation, receipt)
        _require(receipt["slot_id"] == _slot(freeze["schedule"][index]), "SCHEDULE_PREFIX")
        _require(receipt["attempt_id"] not in seen_attempts, "DUPLICATE_ATTEMPT")
        seen_attempts.add(receipt["attempt_id"])
        model = receipt["reported_model"]
        _require(model is None or (isinstance(model, str) and re.fullmatch(r"[A-Za-z0-9._-]{1,120}", model) is not None), "BACKEND_ID")
        if model is not None:
            _require(backend is None or model == backend, "BACKEND_CHANGED")
            backend = model
        if receipt["status"] != "valid":
            _require(index == len(receipts) - 1, "ATTEMPT_AFTER_FAILURE")


def _public_reason(reason: str) -> str:
    reason = re.sub(r"(?i)\b[A-Z]:[\\/][^\s\"']+|\\\\[^\s\"']+|(?<!\w)/(?:[^\s/]+/)+[^\s]*", "[path omitted]", reason)
    reason = re.sub(r"(?<![\w])(?:[\w.-]+[\\/])+[\w.-]+", "[path omitted]", reason)
    reason = re.sub(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "[email omitted]", reason)
    reason = re.sub(r"\b[A-Za-z0-9_-]{24,}\b", "[identifier omitted]", reason)
    return reason


@_boundary
def project_stdout(raw: bytes) -> bytes:
    """Transform parseable producer JSONL into a deterministic safe projection.

    Invalid events become safe invalid placeholders, preserving parser status.
    This transformation does not replace the required human privacy review.
    """
    try:
        lines = raw.decode("utf-8", errors="strict").splitlines()
    except UnicodeDecodeError as error:
        raise EvidenceError("PROJECTION_UTF8") from error
    projected = []
    identifiers: dict[str, str] = {}
    for line in lines:
        if not line.strip():
            continue
        try:
            event = _json(line.encode("utf-8"))
        except EvidenceError:
            projected.append(b"{")
            continue
        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
            projected.append(canonical_json({"type": "unrecognized.event"}))
            continue
        event_type = event["type"]
        allowed = {"thread.started", "turn.started", "item.started", "item.completed", "turn.completed", "turn.failed", "error"}
        if event_type not in allowed:
            projected.append(canonical_json({"type": "unrecognized.event"}))
            continue
        output: dict[str, Any] = {"type": event_type}
        envelope_keys = {"thread.started": {"type", "thread_id"}, "turn.started": {"type"},
                         "item.started": {"type", "item"}, "item.completed": {"type", "item"},
                         "turn.completed": {"type", "usage", "model", "model_id", "thread_id"},
                         "turn.failed": {"type", "error"}, "error": {"type", "message"}}
        if set(event) - envelope_keys[event_type]:
            output["unrecognized"] = True
        if event_type in {"item.started", "item.completed"}:
            item = event.get("item")
            if not isinstance(item, dict):
                output["item"] = None
                projected.append(canonical_json(output))
                continue
            if not isinstance(item.get("type"), str) or item["type"] not in {"reasoning", "agent_message", "error"}:
                output["item"] = {"type": "forbidden_tool"}
                projected.append(canonical_json(output))
                continue
            safe_item = {"type": item["type"]}
            item_keys = {"id", "type", "message"} if item["type"] == "error" else {"id", "type", "text"}
            if set(item) - item_keys:
                safe_item["unrecognized"] = True
            if item.get("id") is not None:
                item_id = item["id"]
                if not isinstance(item_id, str) or not item_id:
                    safe_item["id"] = ""
                else:
                    if item_id not in identifiers:
                        identifiers[item_id] = f"item-{len(identifiers) + 1}"
                    safe_item["id"] = identifiers[item_id]
            if event_type == "item.completed" and item["type"] == "agent_message":
                try:
                    value = _json(item.get("text", "").encode("utf-8")) if isinstance(item.get("text"), str) else None
                except EvidenceError:
                    value = None
                if (isinstance(value, dict) and set(value) == {"verdict", "reason"} and
                        isinstance(value["verdict"], str) and value["verdict"] in {"PASS", "FAIL", "INDETERMINATE"} and
                        isinstance(value["reason"], str) and value["reason"].strip() and len(value["reason"]) <= 300):
                    safe_item["text"] = canonical_json({"verdict": value["verdict"], "reason": _public_reason(value["reason"])}).decode("utf-8")
                else:
                    safe_item["text"] = "invalid structured output"
            output["item"] = safe_item
        if event_type == "turn.completed":
            for key in ("model", "model_id"):
                if key in event:
                    value = event[key]
                    output[key] = value if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9._-]{1,120}", value) else ""
        projected.append(canonical_json(output))
    return b"\n".join(projected) + (b"\n" if projected else b"")


@_boundary
def verify_projection(raw: bytes, projection: bytes, receipt: dict[str, Any], replay: Callable[..., Any]) -> dict[str, Any]:
    """Bind a deterministic public projection to private raw bytes and replay."""
    _require(_digest(raw) == receipt["stdout_sha256"] and len(raw) == receipt["stdout_bytes"], "RAW_CAPTURE_MISMATCH")
    _require(project_stdout(raw) == projection, "PROJECTION_TRANSFORM")
    try:
        private_result = replay(raw.decode("utf-8"), receipt["terminal_exit"], receipt["timed_out"])
        result = replay(projection.decode("utf-8"), receipt["terminal_exit"], receipt["timed_out"])
    except (UnicodeError, ValueError, TypeError) as error:
        raise EvidenceError("PROJECTION_REPLAY_FAILED") from error
    expected = (receipt["status"], receipt["verdict"], _public_reason(receipt["reason"]) if receipt["reason"] is not None else None, receipt["reported_model"])
    _require(_with_custody(private_result, receipt) == (receipt["status"], receipt["verdict"], receipt["reason"], receipt["reported_model"]), "RAW_REPLAY_MISMATCH")
    _require(_with_custody(result, receipt) == expected, "PROJECTION_REPLAY_MISMATCH")
    return {"raw_sha256": _digest(raw), "raw_bytes": len(raw), "projection_sha256": _digest(projection)}


@_boundary
def verify_public_bundle(root: Path, expected_manifest_sha256: str, replay: Callable[..., Any]) -> dict[str, Any]:
    """Reopen a manifest-bound portable projection bundle without CLI or raw files.

    Required files include freeze, study inventory, admission context and receipts,
    and one projection for each study and admission attempt. The manifest stores schema_version,
    freeze_sha256 and an exact relative-path-to-byte-hash map under files.
    """
    root = Path(root).resolve()
    try:
        manifest_bytes = (root / "manifest.json").read_bytes()
    except OSError as error:
        raise EvidenceError("MANIFEST_UNREADABLE") from error
    _require(_sha(expected_manifest_sha256) and _digest(manifest_bytes) == expected_manifest_sha256, "MANIFEST_DIGEST")
    manifest = _json(manifest_bytes)
    _require(isinstance(manifest, dict) and set(manifest) == {"schema_version", "freeze_sha256", "files"} and type(manifest["schema_version"]) is int and manifest["schema_version"] == 1 and isinstance(manifest["files"], dict), "MANIFEST_SCHEMA")
    files: dict[str, bytes] = {}
    for name, digest in manifest["files"].items():
        _require(isinstance(name, str) and _sha(digest), "MANIFEST_ENTRY")
        relative = Path(name)
        _require(not relative.is_absolute() and ".." not in relative.parts and relative.as_posix() == name, "MANIFEST_PATH")
        path = root / relative
        _require(path.resolve().is_relative_to(root) and not path.is_symlink(), "MANIFEST_PATH")
        try:
            data = path.read_bytes()
        except OSError as error:
            raise EvidenceError("PUBLIC_FILE_UNREADABLE") from error
        _require(_digest(data) == digest, "PUBLIC_FILE_DIGEST")
        files[name] = data
    required = {"freeze.json", "reservations.json", "receipts.json", "canary_ledger.json", "admission/context.json",
                "admission/structured.json", "admission/marker.json"}
    _require(required <= set(files), "PUBLIC_FILE_MISSING")
    freeze = _json(files["freeze.json"])
    reservations = _json(files["reservations.json"])
    receipts = _json(files["receipts.json"])
    _require(isinstance(freeze, dict) and freeze_sha256(freeze) == manifest["freeze_sha256"], "PUBLIC_FREEZE_DIGEST")
    _require(set(freeze) == {"schema_version", "frozen_utc", "scientific_files", "scientific_sha256", "protocol", "schedule", "cli", "auth_route", "admission"} and
             type(freeze["schema_version"]) is int and freeze["schema_version"] == 1, "FREEZE_SCHEMA")
    _require(datetime.fromisoformat(freeze["frozen_utc"].replace("Z", "+00:00")).utcoffset().total_seconds() == 0, "FREEZE_TIME")
    _require(isinstance(freeze["scientific_files"], dict) and all(isinstance(k, str) and _sha(v) for k, v in freeze["scientific_files"].items()), "SCIENTIFIC_MAP")
    _require(freeze.get("scientific_sha256") == freeze_sha256(freeze.get("scientific_files")), "PUBLIC_SCIENTIFIC_DIGEST")
    _require(isinstance(freeze["schedule"], list) and _integer(freeze["protocol"]["turn_budget"]["study"]) and
             len(freeze["schedule"]) == freeze["protocol"]["turn_budget"]["study"], "SCHEDULE_BUDGET")
    slots = [_slot(cell) for cell in freeze["schedule"]]
    _require(len(slots) == len(set(slots)), "DUPLICATE_SCHEDULE_SLOT")
    _require(freeze.get("admission", {}).get("status") == "PASS" and freeze["admission"].get("cli") == freeze.get("cli") and
             freeze["admission"].get("scientific_sha256") == freeze.get("scientific_sha256"), "PUBLIC_ADMISSION")
    _require(freeze.get("auth_route") == "chatgpt_subscription", "AUTH_ROUTE")
    _require(_public_cli(freeze["cli"]), "PUBLIC_CLI_SCHEMA")
    context = _json(files["admission/context.json"])
    _require(isinstance(context, dict) and context.get("requested_model") == freeze["protocol"]["model"]["requested_alias"] and
             context.get("reasoning_effort") == freeze["protocol"]["model"]["reasoning_effort"], "PUBLIC_ADMISSION_MODEL")
    admission_receipts = {name: _json(files[f"admission/{name}.json"]) for name in ("structured", "marker")}
    ledger = _json(files["canary_ledger.json"])
    _require(isinstance(ledger, list), "CANARY_LEDGER_SCHEMA")
    seen_canaries = set()
    admitted_ids = {receipt["attempt_id"] for receipt in admission_receipts.values()}
    seen_admitted = set()
    for item in ledger:
        keys = {"attempt_id", "slot_id", "reserved_utc", "context_sha256", "status", "verdict", "receipt_sha256", "sidecar_sha256", "scientific_sha256", "cli", "admitted"}
        _require(isinstance(item, dict) and set(item) == keys and isinstance(item["attempt_id"], str) and
                 re.fullmatch(r"[A-Za-z0-9_-]{1,128}", item["attempt_id"]) is not None and item["attempt_id"] not in seen_canaries, "CANARY_LEDGER_ENTRY")
        seen_canaries.add(item["attempt_id"])
        _require(item["slot_id"] in {"canary:structured", "canary:marker"} and
                 item["status"] in {"valid", "invalid_output", "protocol_invalid", "operational_unknown"} and
                 (item["verdict"] is None or item["verdict"] in {"PASS", "FAIL", "INDETERMINATE"}) and
                 all(_sha(item[key]) for key in ("context_sha256", "receipt_sha256", "sidecar_sha256", "scientific_sha256")) and
                 _public_cli(item["cli"]) and type(item["admitted"]) is bool, "CANARY_LEDGER_ENTRY")
        _require((item["status"] == "valid") == (item["verdict"] is not None), "CANARY_LEDGER_VERDICT")
        _require(datetime.fromisoformat(item["reserved_utc"].replace("Z", "+00:00")).utcoffset().total_seconds() == 0, "CANARY_LEDGER_TIME")
        _require(item["admitted"] == (item["attempt_id"] in admitted_ids), "CANARY_LEDGER_ADMISSION")
        if item["admitted"]:
            name = item["slot_id"].split(":")[1]
            receipt = admission_receipts[name]
            _require(receipt["attempt_id"] == item["attempt_id"] and item["status"] == receipt["status"] and
                     item["verdict"] == receipt["verdict"] and item["context_sha256"] == freeze["admission"]["context_sha256"] and
                     item["sidecar_sha256"] == receipt["sidecar_sha256"] and
                     item["receipt_sha256"] == _digest(files[f"admission/{name}.json"]) and
                     item["scientific_sha256"] == freeze["scientific_sha256"] and item["cli"] == freeze["cli"], "CANARY_LEDGER_JOIN")
            seen_admitted.add(item["attempt_id"])
    _require(seen_admitted == admitted_ids, "CANARY_LEDGER_ADMISSION")
    budget = freeze["protocol"]["turn_budget"]
    _require(_integer(budget["canary"]) and _integer(budget["absolute"]) and
             len(ledger) <= budget["canary"] and len(ledger) + len(reservations) <= budget["absolute"], "PUBLIC_BUDGET")
    def replay_canary(name: str, receipt: dict[str, Any]) -> bool:
        attempt = receipt["attempt_id"]
        path = f"projections/{attempt}.jsonl"
        _require(path in files, "PUBLIC_CANARY_PROJECTION")
        try:
            parsed = replay(files[path].decode("utf-8", errors="strict"), 0, False)
        except (UnicodeError, ValueError, TypeError) as error:
            raise EvidenceError("PUBLIC_CANARY_REPLAY") from error
        _require(_public_reason(receipt["reason"]) == receipt["reason"], "PUBLIC_UNSAFE_REASON")
        return _replayed(parsed)[:3] == ("valid", receipt["verdict"], receipt["reason"])
    verify_admission(freeze["admission"], context,
                     {name: root / "admission" / f"{name}.json" for name in ("structured", "marker")}, replay_canary)
    verify_inventory(freeze, reservations, receipts, manifest["freeze_sha256"])
    _require(not (seen_canaries & {receipt["attempt_id"] for receipt in receipts}), "DUPLICATE_ATTEMPT")
    expected = required | {f"projections/{receipt['attempt_id']}.jsonl" for receipt in receipts} | {
        f"attestations/{receipt['attempt_id']}.json" for receipt in receipts
    } | {
        f"projections/{receipt['attempt_id']}.jsonl" for receipt in admission_receipts.values()
    } | {
        f"attestations/{receipt['attempt_id']}.json" for receipt in admission_receipts.values()
    }
    _require(set(files) == expected, "PUBLIC_FILE_INVENTORY")
    actual = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file() and path != root / "manifest.json"}
    _require(actual == expected, "PUBLIC_UNEXPECTED_FILE")
    for receipt in admission_receipts.values():
        projection = files[f"projections/{receipt['attempt_id']}.jsonl"]
        attestation = _json(files[f"attestations/{receipt['attempt_id']}.json"])
        _require(isinstance(attestation, dict) and set(attestation) == {"raw_sha256", "raw_bytes", "projection_sha256", "sidecar_sha256"} and
                 _sha(attestation["raw_sha256"]) and _integer(attestation["raw_bytes"]) and
                 attestation["projection_sha256"] == _digest(projection) and attestation["sidecar_sha256"] == receipt["sidecar_sha256"], "PUBLIC_CANARY_ATTESTATION")
    for receipt in receipts:
        if receipt["reason"] is not None:
            _require(_public_reason(receipt["reason"]) == receipt["reason"], "PUBLIC_UNSAFE_REASON")
        raw = files[f"projections/{receipt['attempt_id']}.jsonl"]
        attestation = _json(files[f"attestations/{receipt['attempt_id']}.json"])
        _require(attestation == {"raw_sha256": receipt["stdout_sha256"], "raw_bytes": receipt["stdout_bytes"],
                                 "projection_sha256": _digest(raw)}, "PUBLIC_ATTESTATION")
        try:
            result = replay(raw.decode("utf-8", errors="strict"), receipt["terminal_exit"], receipt["timed_out"])
        except (UnicodeError, ValueError, TypeError) as error:
            raise EvidenceError("PUBLIC_REPLAY_FAILED") from error
        expected_result = (receipt["status"], receipt["verdict"], receipt["reason"], receipt["reported_model"])
        _require(_with_custody(result, receipt) == expected_result, "PUBLIC_REPLAY_MISMATCH")
    return {"verification_scope": "public_projection_replay", "freeze_sha256": manifest["freeze_sha256"],
            "freeze": freeze, "reservations": reservations, "admission_context": context, "receipts": receipts, "canary_ledger": ledger,
            "raw_byte_verification": "not independently verifiable from public commitments"}


# Schema 2 is deliberately separate from the retained Codex schema 1 contract.
V2_FREEZE_KEYS = {"schema_version", "frozen_utc", "provider", "auth_route", "scientific_files", "scientific_sha256",
                  "protocol", "schedule", "transport", "history_sha256", "admission"}
V2_STUDY_RECEIPT_KEYS = (RESERVATION_KEYS | {
    "provider", "scientific_sha256", "transport", "history_sha256", "reservation_sha256", "request_sha256",
    "request_bytes", "transport_metadata_sha256", "sidecar_sha256", "input_sha256", "status", "verdict", "reason",
    "reported_model", "terminal_exit", "timed_out", "cleanup_proven", "forced_cleanup", "active_processes_final",
    "judge_directory_cleaned", "stdout_sha256", "stderr_sha256", "stdout_bytes", "stderr_bytes", "timestamp_utc",
    "native_failed_step", "marker_echo", "runtime_before_sha256", "runtime_after_sha256",
})
V2_CONTEXT_KEYS = {"schema_version", "provider", "scientific_sha256", "transport", "history_sha256", "predicates"}
V2_ADMISSION_KEYS = {"schema_version", "provider", "status", "admitted_utc", "scientific_sha256", "transport",
                     "history_sha256", "context_sha256", "receipt_sha256"}
V2_CANARY_RECEIPT_KEYS = {"schema_version", "provider", "attempt_id", "predicate", "context_sha256", "reservation_sha256",
                          "sidecar_sha256", "transport_metadata_sha256", "request_sha256", "request_bytes", "status",
                          "verdict", "reason", "tool_event", "marker_echo", "cleanup_proven", "forced_cleanup",
                          "active_processes_final", "judge_directory_cleaned", "reported_model", "runtime_before_sha256",
                          "runtime_after_sha256"}
V2_HTTP_KEYS = {"schema_version", "endpoint", "route", "request_sha256", "request_bytes", "http_status", "body_complete",
                "body_sha256", "body_bytes", "dispatched", "daemon_completion_uncertain", "failed_step", "last_completed_step", "fault_code"}
V2_SIDECAR_KEYS = {"schema_version", "provider", "attempt_id", "slot_id", "context_sha256", "scientific_sha256", "transport",
                   "history_sha256", "prompt_sha256", "input_sha256", "request_sha256", "request_bytes", "runtime_before", "runtime_after",
                   "status", "verdict", "reason", "reported_model", "terminal_exit", "timed_out", "cleanup_proven", "forced_cleanup",
                   "active_processes_final", "judge_directory_cleaned", "failed_step", "last_completed_step", "fault_code", "marker_echo",
                   "tool_event", "protocol_violations", "stdout_path", "stderr_path", "terminal_path", "metadata_path", "http_metadata_path",
                   "stdout_sha256", "stderr_sha256", "terminal_sha256", "metadata_sha256", "transport_metadata_sha256", "stdout_bytes", "stderr_bytes",
                   "stdout_head_hex", "stdout_tail_hex", "stderr_head_hex", "stderr_tail_hex", "stdout_truncated", "stderr_truncated", "marker",
                   "native_failed_step"}
V2_CANARY_RESERVATION_KEYS = {"schema_version", "attempt_id", "slot_id", "kind", "schedule_index", "reserved_utc", "context_sha256"}


def _v2_version(value: dict[str, Any]) -> bool:
    return type(value.get("schema_version")) is int and value["schema_version"] == 2 and value.get("provider") == "ollama_local"


def _v2_transport(transport: Any, protocol: dict[str, Any]) -> None:
    _require(isinstance(transport, dict) and set(transport) == {"configuration_sha256", "runtime_identity_sha256", "runtime_identity"}, "V2_TRANSPORT_SCHEMA")
    runtime = transport["runtime_identity"]
    _require(_sha(transport["configuration_sha256"]) and isinstance(runtime, dict) and
             set(runtime) == {"endpoint", "observed", "python_version", "python_sha256", "worker_sha256"} and
             runtime["endpoint"] == protocol["transport"]["endpoint"] == "http://127.0.0.1:11434" and
             runtime["observed"] == protocol["transport"]["expected_runtime"] and
             isinstance(runtime["python_version"], str) and bool(runtime["python_version"]) and
             _sha(runtime["python_sha256"]) and _sha(runtime["worker_sha256"]) and
             transport["runtime_identity_sha256"] == freeze_sha256(runtime), "V2_RUNTIME_IDENTITY")


@_boundary
def verify_v2_freeze(
    freeze: dict[str, Any], expected_sha256: str, *, scientific_files: dict[str, str], protocol: dict[str, Any],
    schedule: list[dict[str, Any]], transport: dict[str, Any], history_sha256: str, admission: dict[str, Any],
    verify_admission: Callable[[dict[str, Any]], bool],
) -> str:
    """Join a v2 freeze to reopened static artifacts and independently verified admission."""
    _require(isinstance(freeze, dict) and set(freeze) == V2_FREEZE_KEYS and _v2_version(freeze), "V2_FREEZE_SCHEMA")
    _require(freeze["auth_route"] == "local_unauthenticated" and _sha(expected_sha256) and
             freeze_sha256(freeze) == expected_sha256, "V2_FREEZE_IDENTITY")
    _require(datetime.fromisoformat(freeze["frozen_utc"].replace("Z", "+00:00")).utcoffset().total_seconds() == 0, "V2_FREEZE_TIME")
    _require(freeze["scientific_files"] == scientific_files and freeze["scientific_sha256"] == freeze_sha256(scientific_files) and
             all(isinstance(k, str) and _sha(v) for k, v in scientific_files.items()), "V2_SCIENCE")
    _require(protocol.get("schema_version") == 2 and protocol.get("provider") == "ollama_local" and
             freeze["protocol"] == protocol and freeze["schedule"] == schedule and isinstance(schedule, list), "V2_PROTOCOL")
    _require(len(schedule) == protocol["turn_budget"]["study"] and len({_slot(cell) for cell in schedule}) == len(schedule), "V2_SCHEDULE")
    _v2_transport(transport, protocol)
    _require(freeze["transport"] == transport and _sha(history_sha256) and freeze["history_sha256"] == history_sha256, "V2_IDENTITY_JOIN")
    _require(freeze["admission"] == admission and verify_admission(admission) is True, "V2_ADMISSION")
    return expected_sha256


@_boundary
def verify_v2_admission(
    admission: dict[str, Any], context: dict[str, Any], receipt_paths: dict[str, Path],
    verify_receipt: Callable[[str, dict[str, Any]], bool], *, public_projection: bool = False,
    projected_receipt_bytes: dict[str, bytes] | None = None,
) -> None:
    """Reopen exact canary receipt bytes; caller must independently verify private raw custody."""
    _require(isinstance(context, dict) and set(context) == V2_CONTEXT_KEYS and _v2_version(context), "V2_CONTEXT_SCHEMA")
    _require(_sha(context["scientific_sha256"]) and _sha(context["history_sha256"]), "V2_CONTEXT_IDENTITY")
    predicates = context["predicates"]
    _require(isinstance(predicates, dict) and set(predicates) == {"structured", "marker"}, "V2_PREDICATES")
    structured, marker = predicates["structured"], predicates["marker"]
    _require(set(structured) == {"prompt_sha256", "request_sha256", "request_bytes", "verdict", "reason"} and
             structured["verdict"] == "PASS" and structured["reason"] == "structured response available", "V2_STRUCTURED")
    _require(set(marker) == {"prompt_sha256", "request_sha256", "request_bytes", "marker_sha256", "verdict"} and
             marker["verdict"] == "INDETERMINATE" and _sha(marker["marker_sha256"]), "V2_MARKER")
    for item in (structured, marker):
        _require(_sha(item["prompt_sha256"]) and _sha(item["request_sha256"]) and _integer(item["request_bytes"]), "V2_PREDICATE_INPUT")
    _require(isinstance(admission, dict) and set(admission) == V2_ADMISSION_KEYS and _v2_version(admission) and
             admission["status"] == "PASS" and admission["context_sha256"] == freeze_sha256(context) and
             all(admission[key] == context[key] for key in ("scientific_sha256", "transport", "history_sha256")), "V2_ADMISSION_SCHEMA")
    _require(datetime.fromisoformat(admission["admitted_utc"].replace("Z", "+00:00")).utcoffset().total_seconds() == 0, "V2_ADMISSION_TIME")
    _require(isinstance(admission["receipt_sha256"], dict) and set(admission["receipt_sha256"]) == {"structured", "marker"} and
             set(receipt_paths) == {"structured", "marker"}, "V2_CANARY_RECEIPTS")
    seen = set()
    for name in ("structured", "marker"):
        raw = projected_receipt_bytes[name] if public_projection and projected_receipt_bytes is not None else Path(receipt_paths[name]).read_bytes()
        receipt = _json(raw)
        if public_projection:
            _require(isinstance(receipt, dict) and set(receipt) == V2_CANARY_RECEIPT_KEYS | {"private_receipt_sha256"} and
                     _sha(receipt["private_receipt_sha256"]) and receipt["private_receipt_sha256"] == admission["receipt_sha256"][name], "V2_CANARY_PRIVATE_COMMITMENT")
            receipt = {key: value for key, value in receipt.items() if key != "private_receipt_sha256"}
            _require(isinstance(receipt["reason"], str) and _public_reason(receipt["reason"]) == receipt["reason"], "V2_CANARY_PUBLIC_REASON")
        else:
            _require(_digest(raw) == admission["receipt_sha256"][name], "V2_CANARY_DIGEST")
        _require(isinstance(receipt, dict) and set(receipt) == V2_CANARY_RECEIPT_KEYS and _v2_version(receipt), "V2_CANARY_SCHEMA")
        _require(isinstance(receipt["attempt_id"], str) and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", receipt["attempt_id"]) and
                 receipt["attempt_id"] not in seen, "V2_CANARY_ATTEMPT")
        seen.add(receipt["attempt_id"])
        _require(receipt["predicate"] == name and receipt["context_sha256"] == admission["context_sha256"] and
                 receipt["request_sha256"] == predicates[name]["request_sha256"] and receipt["request_bytes"] == predicates[name]["request_bytes"] and
                 receipt["status"] == "valid" and receipt["verdict"] == predicates[name]["verdict"] and
                 isinstance(receipt["reason"], str) and bool(receipt["reason"].strip()), "V2_CANARY_RESULT")
        if name == "structured":
            _require(receipt["reason"] == structured["reason"], "V2_CANARY_REASON")
        _require(receipt["tool_event"] is False and receipt["marker_echo"] is False and receipt["cleanup_proven"] is True and
                 receipt["forced_cleanup"] is False and type(receipt["active_processes_final"]) is int and
                 receipt["active_processes_final"] == 0 and receipt["judge_directory_cleaned"] is True and
                 receipt["reported_model"] == context["transport"]["runtime_identity"]["observed"]["model"] and
                 receipt["runtime_before_sha256"] == receipt["runtime_after_sha256"] == context["transport"]["runtime_identity_sha256"] and
                 all(_sha(receipt[key]) for key in ("reservation_sha256", "sidecar_sha256", "transport_metadata_sha256")), "V2_CANARY_CUSTODY")
        _require(verify_receipt(name, receipt) is True, "V2_CANARY_PRIVATE_VERIFICATION")


def _v2_study_receipt(freeze: dict[str, Any], freeze_hash: str, reservation: dict[str, Any], receipt: dict[str, Any]) -> None:
    _require(isinstance(reservation, dict) and set(reservation) == RESERVATION_KEYS and
             type(reservation["schema_version"]) is int and reservation["schema_version"] == 1 and reservation["kind"] == "study", "V2_RESERVATION")
    _require(isinstance(receipt, dict) and set(receipt) == V2_STUDY_RECEIPT_KEYS and _v2_version(receipt), "V2_RECEIPT")
    _require(all(receipt[key] == reservation[key] for key in RESERVATION_KEYS - {"schema_version"}) and
             reservation["freeze_sha256"] == freeze_hash, "V2_RESERVATION_JOIN")
    index = reservation["schedule_index"]
    _require(_integer(index) and index < len(freeze["schedule"]) and _slot(freeze["schedule"][index]) == reservation["slot_id"], "V2_SLOT")
    _require(isinstance(receipt["attempt_id"], str) and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", receipt["attempt_id"]), "V2_ATTEMPT")
    cell = freeze["schedule"][index]
    expected_inputs = {key: cell[f"{key}_sha256"] for key in ("code", "task", "criteria", "common_prompt", "prompt")}
    _require(receipt["input_sha256"] == expected_inputs and all(_sha(value) for value in expected_inputs.values()), "V2_INPUT")
    _require(receipt["scientific_sha256"] == freeze["scientific_sha256"] and receipt["transport"] == freeze["transport"] and
             receipt["history_sha256"] == freeze["history_sha256"] and
             all(_sha(receipt[key]) for key in ("reservation_sha256", "sidecar_sha256", "request_sha256")) and
             _integer(receipt["request_bytes"]) and receipt["runtime_before_sha256"] == freeze["transport"]["runtime_identity_sha256"] and
             (receipt["runtime_after_sha256"] is None or _sha(receipt["runtime_after_sha256"])), "V2_RECEIPT_IDENTITY")
    for key in ("reserved_utc", "timestamp_utc"):
        _require(datetime.fromisoformat(receipt[key].replace("Z", "+00:00")).utcoffset().total_seconds() == 0, "V2_RECEIPT_TIME")
    _require(receipt["status"] in {"valid", "invalid_output", "protocol_invalid", "operational_unknown"}, "V2_STATUS")
    if receipt["status"] == "valid":
        _require(receipt["verdict"] in {"PASS", "FAIL", "INDETERMINATE"} and isinstance(receipt["reason"], str) and
                 bool(receipt["reason"].strip()) and receipt["reported_model"] == freeze["protocol"]["model"]["requested_alias"] and
                 type(receipt["terminal_exit"]) is int and receipt["terminal_exit"] == 0 and receipt["timed_out"] is False and
                 receipt["cleanup_proven"] is True and receipt["forced_cleanup"] is False and
                 type(receipt["active_processes_final"]) is int and receipt["active_processes_final"] == 0 and
                 receipt["judge_directory_cleaned"] is True and receipt["native_failed_step"] is None and receipt["marker_echo"] is False and
                 receipt["runtime_after_sha256"] == freeze["transport"]["runtime_identity_sha256"] and
                 all(_sha(receipt[key]) for key in ("stdout_sha256", "stderr_sha256", "transport_metadata_sha256")) and
                 all(_integer(receipt[key]) for key in ("stdout_bytes", "stderr_bytes")), "V2_VALID_CUSTODY")
    else:
        _require(receipt["verdict"] is None and receipt["reason"] is None, "V2_FAILED_VERDICT")


@_boundary
def verify_v2_inventory(freeze: dict[str, Any], reservations: list[dict[str, Any]], receipts: list[dict[str, Any]], freeze_hash: str) -> None:
    """Validate the whole ordered study prefix; raw files are verified separately."""
    _require(isinstance(reservations, list) and isinstance(receipts, list) and
             len(reservations) == len(receipts) <= len(freeze["schedule"]), "V2_INVENTORY")
    attempts = set()
    for index, (reservation, receipt) in enumerate(zip(reservations, receipts)):
        _v2_study_receipt(freeze, freeze_hash, reservation, receipt)
        _require(reservation["schedule_index"] == index and receipt["attempt_id"] not in attempts, "V2_PREFIX")
        attempts.add(receipt["attempt_id"])
        if receipt["status"] != "valid":
            _require(index == len(receipts) - 1, "V2_ATTEMPT_AFTER_FAILURE")


def _v2_capture_path(root: Path, value: Any) -> Path:
    _require(isinstance(value, str), "V2_CAPTURE_MISSING")
    path = Path(value).resolve()
    _require(path.is_relative_to(root.resolve()) and path.is_file(), "V2_CAPTURE_PATH")
    return path


def _v2_sidecar_types(sidecar: dict[str, Any]) -> None:
    for key in ("timed_out", "cleanup_proven", "forced_cleanup", "judge_directory_cleaned", "marker_echo", "tool_event", "stdout_truncated", "stderr_truncated"):
        _require(sidecar[key] is None or type(sidecar[key]) is bool, "V2_SIDECAR_TYPE")
    for key in ("terminal_exit", "active_processes_final", "stdout_bytes", "stderr_bytes"):
        _require(sidecar[key] is None or type(sidecar[key]) is int, "V2_SIDECAR_TYPE")
    _require(isinstance(sidecar["protocol_violations"], list) and all(isinstance(value, str) for value in sidecar["protocol_violations"]), "V2_SIDECAR_TYPE")


def _v2_http(http: Any) -> None:
    _require(isinstance(http, dict) and set(http) == V2_HTTP_KEYS and type(http["schema_version"]) is int and
             http["schema_version"] == 1 and http["endpoint"] == "http://127.0.0.1:11434" and http["route"] == "/api/chat" and
             _sha(http["request_sha256"]) and _integer(http["request_bytes"]) and _sha(http["body_sha256"]) and _integer(http["body_bytes"]) and
             (http["http_status"] is None or (type(http["http_status"]) is int and 100 <= http["http_status"] <= 599)) and
             all(type(http[key]) is bool for key in ("body_complete", "dispatched", "daemon_completion_uncertain")) and
             all(http[key] is None or (isinstance(http[key], str) and len(http[key]) <= 128) for key in ("failed_step", "fault_code")) and
             isinstance(http["last_completed_step"], str) and 0 < len(http["last_completed_step"]) <= 128, "V2_HTTP_SCHEMA")


def _v2_request(raw: bytes, protocol: dict[str, Any], prompt_sha256: str) -> None:
    value = _json(raw)
    controls = protocol["transport"]["request"]
    _require(isinstance(value, dict) and set(value) == set(controls) | {"model", "messages", "format"} and
             all(canonical_json(value[key]) == canonical_json(controls[key]) for key in controls) and
             value["model"] == protocol["model"]["requested_alias"] and
             value["format"] == _json((Path(__file__).parent / "output.schema.json").read_bytes()) and
             isinstance(value["messages"], list) and len(value["messages"]) == 1 and
             isinstance(value["messages"][0], dict) and set(value["messages"][0]) == {"role", "content"} and
             value["messages"][0]["role"] == "user" and isinstance(value["messages"][0]["content"], str) and
             _digest(value["messages"][0]["content"].encode("utf-8")) == prompt_sha256 and
             canonical_json(value) == raw, "V2_REQUEST_CONTENT")


def _v2_read_stream(path: Path, sidecar: dict[str, Any], name: str, marker: bytes | None = None) -> tuple[bytes | None, bool]:
    digest = hashlib.sha256()
    count = 0
    head, tail, overlap = b"", b"", b""
    body = bytearray() if name == "stdout" else None
    echo = False
    with path.open("rb") as stream:
        while chunk := stream.read(65536):
            count += len(chunk)
            digest.update(chunk)
            head = (head + chunk)[:4096]
            tail = (tail + chunk)[-4096:]
            if marker:
                echo |= marker in overlap + chunk
                overlap = (overlap + chunk)[-(len(marker) - 1):] if len(marker) > 1 else b""
            if body is not None:
                _require(count <= 8 * 1024 * 1024, "V2_CAPTURE_TOO_LARGE")
                body.extend(chunk)
    _require(digest.hexdigest() == sidecar[f"{name}_sha256"] and count == sidecar[f"{name}_bytes"] and
             head.hex() == sidecar[f"{name}_head_hex"] and tail.hex() == sidecar[f"{name}_tail_hex"] and
             sidecar[f"{name}_truncated"] is (count > 4096), "V2_CAPTURE_DIGEST")
    return (bytes(body) if body is not None else None), echo


@_boundary
def verify_v2_private_receipt(
    freeze: dict[str, Any], freeze_hash: str, reservation_path: Path, receipt_path: Path, sidecar_path: Path,
    root: Path, expected_request: bytes, parse_response: Callable[..., Any],
) -> dict[str, Any]:
    """Reopen reservation, sidecar, raw body, native and HTTP metadata; replay offline."""
    root = Path(root).resolve()
    reservation_path = _v2_capture_path(root, str(reservation_path))
    receipt_path = _v2_capture_path(root, str(receipt_path))
    sidecar_path = _v2_capture_path(root, str(sidecar_path))
    reservation_bytes, receipt_bytes, sidecar_bytes = reservation_path.read_bytes(), receipt_path.read_bytes(), sidecar_path.read_bytes()
    reservation, receipt, sidecar = _json(reservation_bytes), _json(receipt_bytes), _json(sidecar_bytes)
    _v2_study_receipt(freeze, freeze_hash, reservation, receipt)
    _require(_digest(reservation_bytes) == receipt["reservation_sha256"] and _digest(sidecar_bytes) == receipt["sidecar_sha256"], "V2_PRIVATE_DIGEST")
    _require(isinstance(sidecar, dict) and set(sidecar) == V2_SIDECAR_KEYS and _v2_version(sidecar), "V2_SIDECAR")
    _v2_sidecar_types(sidecar)
    _require(sidecar["attempt_id"] == receipt["attempt_id"] and sidecar["slot_id"] == receipt["slot_id"] and
             sidecar["context_sha256"] == freeze_hash and all(sidecar[key] == receipt[key] for key in (
                 "scientific_sha256", "transport", "history_sha256", "input_sha256", "request_sha256", "request_bytes",
                 "status", "verdict", "reason", "reported_model", "terminal_exit", "timed_out", "cleanup_proven", "forced_cleanup",
                 "active_processes_final", "judge_directory_cleaned", "stdout_sha256", "stderr_sha256", "stdout_bytes", "stderr_bytes",
                 "transport_metadata_sha256", "native_failed_step", "marker_echo")) and
             sidecar["prompt_sha256"] == receipt["input_sha256"]["prompt"], "V2_SIDECAR_JOIN")
    _require(isinstance(expected_request, bytes) and _digest(expected_request) == receipt["request_sha256"] and
             len(expected_request) == receipt["request_bytes"] and sidecar["marker"] is None, "V2_REQUEST")
    _v2_request(expected_request, freeze["protocol"], receipt["input_sha256"]["prompt"])
    runtime = freeze["transport"]["runtime_identity"]
    _require(sidecar["runtime_before"] == runtime and receipt["runtime_before_sha256"] == freeze_sha256(runtime), "V2_RUNTIME_BEFORE")
    _require(receipt["runtime_after_sha256"] == (freeze_sha256(sidecar["runtime_after"]) if sidecar["runtime_after"] is not None else None), "V2_RUNTIME_AFTER_HASH")
    if receipt["status"] == "valid":
        _require(sidecar["runtime_after"] == runtime, "V2_RUNTIME_AFTER")
    else:
        _require(sidecar["runtime_after"] is None or isinstance(sidecar["runtime_after"], dict), "V2_RUNTIME_AFTER")
    stdout, _ = _v2_read_stream(_v2_capture_path(root, sidecar["stdout_path"]), sidecar, "stdout")
    _v2_read_stream(_v2_capture_path(root, sidecar["stderr_path"]), sidecar, "stderr")
    files = {"stdout": stdout}
    for name, pathkey, hashkey in (("terminal", "terminal_path", "terminal_sha256"), ("metadata", "metadata_path", "metadata_sha256"),
                                   ("http", "http_metadata_path", "transport_metadata_sha256")):
        path = _v2_capture_path(root, sidecar[pathkey])
        _require(path.stat().st_size <= 8 * 1024 * 1024, "V2_CAPTURE_TOO_LARGE")
        files[name] = path.read_bytes()
        _require(_digest(files[name]) == sidecar[hashkey], "V2_CAPTURE_DIGEST")
    terminal, process, http = _json(files["terminal"]), _json(files["metadata"]), _json(files["http"])
    _require(isinstance(terminal, dict) and set(terminal) == {"returncode", "failed_step", "fault_code"} and
             terminal["returncode"] == receipt["terminal_exit"] and
             isinstance(process, dict) and all(type(process.get(key)) is int and process[key] > 0 for key in ("wrapper_pid", "cli_pid")), "V2_NATIVE_RECORD")
    if receipt["status"] == "valid":
        _require(type(terminal["returncode"]) is int and terminal["returncode"] == 0 and terminal["failed_step"] is None and terminal["fault_code"] is None, "V2_TERMINAL_SUCCESS")
    _v2_http(http)
    _require(http["request_sha256"] == receipt["request_sha256"] and http["request_bytes"] == receipt["request_bytes"] and
             http["body_sha256"] == receipt["stdout_sha256"] and http["body_bytes"] == receipt["stdout_bytes"], "V2_HTTP_RECORD")
    facts = dict(http, terminal_exit=receipt["terminal_exit"], timed_out=receipt["timed_out"], cleanup_proven=receipt["cleanup_proven"],
                 forced_cleanup=receipt["forced_cleanup"], active_processes_final=receipt["active_processes_final"], native_failed_step=receipt["native_failed_step"])
    parsed = parse_response(files["stdout"], facts, freeze["protocol"]["model"]["requested_alias"])
    _require(parsed.tool_event == sidecar["tool_event"] and list(parsed.protocol_violations) == sidecar["protocol_violations"], "V2_RAW_FLAGS")
    actual = _replayed(parsed)
    if sidecar["runtime_after"] != runtime or receipt["judge_directory_cleaned"] is not True:
        actual = ("operational_unknown", None, None, actual[3])
    _require(actual == tuple(receipt[key] for key in ("status", "verdict", "reason", "reported_model")), "V2_RAW_REPLAY")
    return {"verification_scope": "private_raw_verified", "receipt": receipt, "http_metadata": http}


@_boundary
def verify_v2_private_canary(
    context: dict[str, Any], reservation_path: Path, receipt_path: Path, sidecar_path: Path,
    root: Path, expected_request: bytes, parse_response: Callable[..., Any],
) -> dict[str, Any]:
    """Reopen a v2 canary's exact request, capture, runtime and native/HTTP records."""
    root = Path(root).resolve()
    reservation_bytes = _v2_capture_path(root, str(reservation_path)).read_bytes()
    receipt_bytes = _v2_capture_path(root, str(receipt_path)).read_bytes()
    sidecar_bytes = _v2_capture_path(root, str(sidecar_path)).read_bytes()
    reservation, receipt, sidecar = _json(reservation_bytes), _json(receipt_bytes), _json(sidecar_bytes)
    _require(isinstance(reservation, dict) and set(reservation) == V2_CANARY_RESERVATION_KEYS and
             type(reservation["schema_version"]) is int and reservation["schema_version"] == 1 and
             reservation["kind"] == "canary" and reservation["schedule_index"] is None, "V2_CANARY_RESERVATION")
    _require(isinstance(receipt, dict) and set(receipt) == V2_CANARY_RECEIPT_KEYS and _v2_version(receipt) and
             isinstance(sidecar, dict) and set(sidecar) == V2_SIDECAR_KEYS and _v2_version(sidecar), "V2_CANARY_PRIVATE_SCHEMA")
    _v2_sidecar_types(sidecar)
    _require(datetime.fromisoformat(reservation["reserved_utc"].replace("Z", "+00:00")).utcoffset().total_seconds() == 0, "V2_CANARY_RESERVED_TIME")
    name = receipt["predicate"]
    _require(name in {"structured", "marker"} and reservation["slot_id"] == f"canary:{name}" and
             reservation["attempt_id"] == receipt["attempt_id"] == sidecar["attempt_id"] and
             sidecar["slot_id"] == reservation["slot_id"] and
             reservation["context_sha256"] == receipt["context_sha256"] == sidecar["context_sha256"] == freeze_sha256(context) and
             receipt["reservation_sha256"] == _digest(reservation_bytes) and receipt["sidecar_sha256"] == _digest(sidecar_bytes), "V2_CANARY_PRIVATE_JOIN")
    predicate = context["predicates"][name]
    _require(sidecar["scientific_sha256"] == context["scientific_sha256"] and sidecar["transport"] == context["transport"] and
             sidecar["history_sha256"] == context["history_sha256"] and sidecar["prompt_sha256"] == predicate["prompt_sha256"] and
             sidecar["input_sha256"] == {"prompt": predicate["prompt_sha256"]} and
             sidecar["request_sha256"] == receipt["request_sha256"] == predicate["request_sha256"] == _digest(expected_request) and
             sidecar["request_bytes"] == receipt["request_bytes"] == predicate["request_bytes"] == len(expected_request), "V2_CANARY_REQUEST")
    from .data import load_protocol
    _v2_request(expected_request, load_protocol(), predicate["prompt_sha256"])
    marker = sidecar["marker"]
    if name == "marker":
        _require(isinstance(marker, str) and bool(marker) and _digest(marker.encode("utf-8")) == predicate["marker_sha256"] and
                 marker.encode("utf-8") not in expected_request, "V2_MARKER_REQUEST")
    else:
        _require(marker is None, "V2_STRUCTURED_MARKER")
    for key in ("status", "verdict", "reason", "reported_model", "tool_event", "marker_echo", "cleanup_proven", "forced_cleanup",
                "active_processes_final", "judge_directory_cleaned", "transport_metadata_sha256"):
        _require(sidecar[key] == receipt[key], "V2_CANARY_FACTS")
    runtime = context["transport"]["runtime_identity"]
    after = sidecar["runtime_after"]
    _require(sidecar["runtime_before"] == runtime and receipt["runtime_before_sha256"] == freeze_sha256(runtime) and
             (after is None or isinstance(after, dict)) and
             receipt["runtime_after_sha256"] == (freeze_sha256(after) if after is not None else None), "V2_CANARY_RUNTIME")
    if receipt["status"] == "valid":
        _require(after == runtime, "V2_CANARY_RUNTIME_AFTER")
    marker_bytes = marker.encode("utf-8") if marker is not None else None
    stdout, stdout_echo = _v2_read_stream(_v2_capture_path(root, sidecar["stdout_path"]), sidecar, "stdout", marker_bytes)
    _, stderr_echo = _v2_read_stream(_v2_capture_path(root, sidecar["stderr_path"]), sidecar, "stderr", marker_bytes)
    files = {"stdout": stdout}
    for name_, pathkey, hashkey in (("terminal", "terminal_path", "terminal_sha256"), ("metadata", "metadata_path", "metadata_sha256"),
                                    ("http", "http_metadata_path", "transport_metadata_sha256")):
        path = _v2_capture_path(root, sidecar[pathkey])
        _require(path.stat().st_size <= 8 * 1024 * 1024, "V2_CAPTURE_TOO_LARGE")
        files[name_] = path.read_bytes()
        _require(_digest(files[name_]) == sidecar[hashkey], "V2_CANARY_CAPTURE_DIGEST")
    echo = stdout_echo or stderr_echo
    _require(receipt["marker_echo"] is echo, "V2_MARKER_ECHO")
    terminal, process, http = _json(files["terminal"]), _json(files["metadata"]), _json(files["http"])
    _require(isinstance(terminal, dict) and set(terminal) == {"returncode", "failed_step", "fault_code"} and
             type(terminal.get("returncode")) is int and terminal["returncode"] == sidecar["terminal_exit"] and
             isinstance(process, dict) and all(type(process.get(key)) is int and process[key] > 0 for key in ("wrapper_pid", "cli_pid")), "V2_CANARY_NATIVE")
    if receipt["status"] == "valid":
        _require(terminal["returncode"] == 0 and terminal["failed_step"] is None and terminal["fault_code"] is None, "V2_CANARY_TERMINAL_SUCCESS")
    _v2_http(http)
    _require(http["request_sha256"] == _digest(expected_request) and http["request_bytes"] == len(expected_request) and
             http["body_sha256"] == _digest(files["stdout"]) and http["body_bytes"] == len(files["stdout"]), "V2_CANARY_HTTP")
    facts = dict(http, terminal_exit=sidecar["terminal_exit"], timed_out=sidecar["timed_out"], cleanup_proven=sidecar["cleanup_proven"],
                 forced_cleanup=sidecar["forced_cleanup"], active_processes_final=sidecar["active_processes_final"], native_failed_step=sidecar["native_failed_step"])
    parsed = parse_response(files["stdout"], facts, runtime["observed"]["model"])
    actual = _replayed(parsed)
    if after != runtime or receipt["judge_directory_cleaned"] is not True:
        actual = ("operational_unknown", None, None, actual[3])
    elif echo and actual[0] != "operational_unknown":
        actual = ("protocol_invalid", None, None, actual[3])
    _require(actual == tuple(receipt[key] for key in ("status", "verdict", "reason", "reported_model")) and
             parsed.tool_event == receipt["tool_event"] and list(parsed.protocol_violations) == sidecar["protocol_violations"], "V2_CANARY_RAW_REPLAY")
    return {"verification_scope": "private_raw_verified", "receipt": receipt, "http_metadata": http}


V2_PUBLIC_CANARY_LEDGER_KEYS = {"attempt_id", "provider", "kind", "slot_id", "reserved_utc", "context_sha256", "status", "verdict",
                                "reservation_sha256", "receipt_sha256", "sidecar_sha256", "admitted"}


def _v2_public_projection(receipt: dict[str, Any], projection: bytes, http_bytes: bytes, attestation_bytes: bytes,
                          expected_model: str, parse_projection: Callable[..., Any], *, canary: bool) -> None:
    http, attestation, projected = _json(http_bytes), _json(attestation_bytes), _json(projection)
    _v2_http(http)
    _require(_digest(http_bytes) == receipt["transport_metadata_sha256"] and http["request_sha256"] == receipt["request_sha256"] and
             http["request_bytes"] == receipt["request_bytes"], "V2_PUBLIC_HTTP")
    _require(isinstance(attestation, dict) and set(attestation) == {"raw_sha256", "raw_bytes", "projection_sha256", "transport_metadata_sha256"} and
             _sha(attestation["raw_sha256"]) and _integer(attestation["raw_bytes"]) and
             attestation["raw_sha256"] == http["body_sha256"] and attestation["raw_bytes"] == http["body_bytes"] and
             attestation["projection_sha256"] == _digest(projection) and attestation["transport_metadata_sha256"] == _digest(http_bytes), "V2_PUBLIC_ATTESTATION")
    if not canary:
        _require(attestation["raw_sha256"] == receipt["stdout_sha256"] and attestation["raw_bytes"] == receipt["stdout_bytes"], "V2_PUBLIC_BODY_JOIN")
    _require(isinstance(projected, dict) and isinstance(projected.get("facts"), dict) and
             isinstance(projected["facts"].get("transport_checks"), dict), "V2_PUBLIC_PROJECTION_SCHEMA")
    checks = projected["facts"]["transport_checks"]
    expected_checks = {
        "native_exit": True if canary else type(receipt["terminal_exit"]) is int and receipt["terminal_exit"] == 0,
        "no_timeout": True if canary else receipt["timed_out"] is False,
        "cleanup": receipt["cleanup_proven"] is True, "no_forced_cleanup": receipt["forced_cleanup"] is False,
        "no_active_processes": type(receipt["active_processes_final"]) is int and receipt["active_processes_final"] == 0,
        "http_status": type(http["http_status"]) is int and http["http_status"] == 200,
        "body_complete": http["body_complete"] is True, "daemon_certain": http["daemon_completion_uncertain"] is False,
        "dispatched": http["dispatched"] is True, "http_step": http["failed_step"] is None,
        "native_step": True if canary else receipt["native_failed_step"] is None,
        "endpoint": True, "route": True, "schema": True, "body_hash": True, "body_size": True,
    }
    _require(checks == expected_checks, "V2_PUBLIC_TRANSPORT_CHECKS")
    parsed = parse_projection(projection, expected_model)
    actual = _replayed(parsed)
    if not canary and (receipt["runtime_after_sha256"] != receipt["runtime_before_sha256"] or receipt["judge_directory_cleaned"] is not True):
        actual = ("operational_unknown", None, None, actual[3])
    elif receipt["marker_echo"] is True and actual[0] != "operational_unknown":
        actual = ("protocol_invalid", None, None, actual[3])
    expected = tuple(receipt[key] for key in ("status", "verdict", "reason", "reported_model"))
    _require(actual == expected, "V2_PUBLIC_REPLAY")


@_boundary
def verify_v2_public_bundle(root: Path, expected_manifest_sha256: str, parse_projection: Callable[..., Any]) -> dict[str, Any]:
    """Verify exact public files and Ollama projections without private raw or a daemon."""
    from .history import ATTEMPT_IDS

    root = Path(root).resolve()
    manifest_bytes = (root / "manifest.json").read_bytes()
    _require(_sha(expected_manifest_sha256) and _digest(manifest_bytes) == expected_manifest_sha256, "V2_PUBLIC_MANIFEST_DIGEST")
    manifest = _json(manifest_bytes)
    _require(isinstance(manifest, dict) and set(manifest) == {"schema_version", "provider", "freeze_sha256", "files"} and
             _v2_version(manifest) and isinstance(manifest["files"], dict), "V2_PUBLIC_MANIFEST")
    files = {}
    for name, checksum in manifest["files"].items():
        _require(isinstance(name, str) and _sha(checksum), "V2_PUBLIC_ENTRY")
        relative = Path(name)
        _require(not relative.is_absolute() and ".." not in relative.parts and relative.as_posix() == name, "V2_PUBLIC_PATH")
        path = root / relative
        _require(path.resolve().is_relative_to(root) and not path.is_symlink(), "V2_PUBLIC_PATH")
        raw = path.read_bytes()
        _require(_digest(raw) == checksum, "V2_PUBLIC_FILE_DIGEST")
        files[name] = raw
    required = {"freeze.json", "reservations.json", "receipts.json", "history.json", "canary_ledger.json", "admission/context.json",
                "admission/structured.json", "admission/marker.json"}
    _require(required <= set(files), "V2_PUBLIC_FILES")
    freeze, reservations, receipts, history, ledger, context = (_json(files[name]) for name in (
        "freeze.json", "reservations.json", "receipts.json", "history.json", "canary_ledger.json", "admission/context.json"))
    _require(isinstance(freeze, dict) and set(freeze) == V2_FREEZE_KEYS and _v2_version(freeze) and
             freeze["auth_route"] == "local_unauthenticated" and freeze_sha256(freeze) == manifest["freeze_sha256"] and
             freeze["scientific_sha256"] == freeze_sha256(freeze["scientific_files"]) and
             freeze["history_sha256"] == _digest(files["history.json"]), "V2_PUBLIC_FREEZE")
    _require(isinstance(freeze["protocol"], dict) and _v2_version(freeze["protocol"]) and isinstance(freeze["schedule"], list) and
             _integer(freeze["protocol"]["turn_budget"]["study"]) and len(freeze["schedule"]) == freeze["protocol"]["turn_budget"]["study"] and
             len({_slot(cell) for cell in freeze["schedule"]}) == len(freeze["schedule"]), "V2_PUBLIC_PROTOCOL")
    _v2_transport(freeze["transport"], freeze["protocol"])
    _require(isinstance(history, dict) and set(history) == {"schema_version", "provider", "attempts"} and
             type(history["schema_version"]) is int and history["schema_version"] == 1 and history["provider"] == "codex_v1" and
             isinstance(history["attempts"], list) and [row.get("attempt_id") for row in history["attempts"]] == list(ATTEMPT_IDS), "V2_PUBLIC_HISTORY")
    historical = {row["attempt_id"]: row for row in history["attempts"]}
    for row in historical.values():
        _require(set(row) == {"attempt_id", "provider", "context_sha256", "scientific_sha256", "configuration_sha256", "status", "admitted", "artifacts_sha256"} and
                 row["provider"] == "codex_v1" and row["admitted"] is False and row["status"] in {"protocol_invalid", "operational_unknown"} and
                 all(_sha(row[key]) for key in ("context_sha256", "scientific_sha256", "configuration_sha256")) and
                 isinstance(row["artifacts_sha256"], dict) and set(row["artifacts_sha256"]) == {"reservation", "receipt", "sidecar", "stdout", "stderr", "terminal", "metadata"} and
                 all(_sha(value) for value in row["artifacts_sha256"].values()), "V2_PUBLIC_HISTORY_ENTRY")
    verify_v2_inventory(freeze, reservations, receipts, manifest["freeze_sha256"])
    admission = freeze["admission"]
    canaries = {name: _json(files[f"admission/{name}.json"]) for name in ("structured", "marker")}
    admitted_ids = {canaries[name]["attempt_id"] for name in canaries}
    _require(isinstance(ledger, list), "V2_PUBLIC_LEDGER")
    seen = set()
    for row in ledger:
        _require(isinstance(row, dict) and set(row) == V2_PUBLIC_CANARY_LEDGER_KEYS and
                 isinstance(row["attempt_id"], str) and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", row["attempt_id"]) and
                 row["attempt_id"] not in seen and row["kind"] == "canary" and row["slot_id"] in {"canary:structured", "canary:marker"} and
                 row["status"] in {"valid", "invalid_output", "protocol_invalid", "operational_unknown"} and
                 (row["verdict"] is None or row["verdict"] in {"PASS", "FAIL", "INDETERMINATE"}) and
                 type(row["admitted"]) is bool and all(_sha(row[key]) for key in ("context_sha256", "reservation_sha256", "receipt_sha256", "sidecar_sha256")), "V2_PUBLIC_LEDGER_ENTRY")
        seen.add(row["attempt_id"])
        _require(datetime.fromisoformat(row["reserved_utc"].replace("Z", "+00:00")).utcoffset() is not None, "V2_PUBLIC_LEDGER_TIME")
        if row["provider"] == "codex_v1":
            _require(row["attempt_id"] in historical and row["admitted"] is False and row["verdict"] is None and
                     row["context_sha256"] == historical[row["attempt_id"]]["context_sha256"] and row["status"] == historical[row["attempt_id"]]["status"] and
                     row["reservation_sha256"] == historical[row["attempt_id"]]["artifacts_sha256"]["reservation"] and
                     row["receipt_sha256"] == historical[row["attempt_id"]]["artifacts_sha256"]["receipt"] and
                     row["sidecar_sha256"] == historical[row["attempt_id"]]["artifacts_sha256"]["sidecar"], "V2_PUBLIC_LEGACY_JOIN")
        else:
            _require(row["provider"] == "ollama_local" and row["attempt_id"] not in historical and
                     row["admitted"] == (row["attempt_id"] in admitted_ids), "V2_PUBLIC_PROVIDER")
            if row["admitted"]:
                name = row["slot_id"].split(":")[1]
                _require(canaries[name]["attempt_id"] == row["attempt_id"] and row["context_sha256"] == admission["context_sha256"] and
                         row["status"] == canaries[name]["status"] and row["verdict"] == canaries[name]["verdict"] and
                         row["reservation_sha256"] == canaries[name]["reservation_sha256"] and
                         row["receipt_sha256"] == canaries[name]["private_receipt_sha256"] and
                         row["sidecar_sha256"] == canaries[name]["sidecar_sha256"], "V2_PUBLIC_CANARY_JOIN")
    _require(set(historical) <= seen and admitted_ids <= seen and not (seen & {r["attempt_id"] for r in receipts}), "V2_PUBLIC_LEDGER_INVENTORY")
    budget = freeze["protocol"]["turn_budget"]
    _require(len(ledger) <= budget["canary"] and len(ledger) + len(receipts) <= budget["absolute"], "V2_PUBLIC_BUDGET")
    def verify_canary(name: str, receipt: dict[str, Any]) -> bool:
        attempt = receipt["attempt_id"]
        _v2_public_projection(receipt, files[f"projections/{attempt}.json"], files[f"transport/{attempt}.json"],
                              files[f"attestations/{attempt}.json"], freeze["protocol"]["model"]["requested_alias"], parse_projection, canary=True)
        return True
    verify_v2_admission(admission, context, {name: root / "admission" / f"{name}.json" for name in canaries}, verify_canary,
                        public_projection=True, projected_receipt_bytes={name: files[f"admission/{name}.json"] for name in canaries})
    _require(context["scientific_sha256"] == freeze["scientific_sha256"] and context["transport"] == freeze["transport"] and
             context["history_sha256"] == freeze["history_sha256"], "V2_PUBLIC_ADMISSION_IDENTITY")
    all_receipts = receipts + list(canaries.values())
    expected = required | {f"{folder}/{receipt['attempt_id']}.json" for receipt in all_receipts for folder in ("projections", "transport", "attestations")}
    _require(set(files) == expected and {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p != root / "manifest.json"} == expected, "V2_PUBLIC_INVENTORY")
    for receipt in receipts:
        attempt = receipt["attempt_id"]
        _v2_public_projection(receipt, files[f"projections/{attempt}.json"], files[f"transport/{attempt}.json"],
                              files[f"attestations/{attempt}.json"], freeze["protocol"]["model"]["requested_alias"], parse_projection, canary=False)
    return {"verification_scope": "public_projection_replay", "freeze_sha256": manifest["freeze_sha256"], "freeze": freeze,
            "reservations": reservations, "receipts": receipts, "history": history, "history_sha256": freeze["history_sha256"], "admission_context": context,
            "canary_ledger": ledger, "canary_reservations": [{key: row[key] for key in ("attempt_id", "kind", "slot_id", "reserved_utc", "context_sha256")} for row in ledger],
            "raw_byte_verification": "not independently verifiable from public commitments"}
