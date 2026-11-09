"""Preflight and immutable, serial admission and study attempt lifecycle."""

from __future__ import annotations

import hashlib
import json
import os
import random
import secrets
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import codex_cli, evidence, history, ollama
from .data import ROOT, load_cases, load_protocol
from .prompt import COMMON_PROMPT, build_prompt
from .protocol import TASK_TMP, canonical_json, sha256_bytes, validate_protocol


REPO_ROOT = ROOT.parent
PREFLIGHT_PATH = TASK_TMP / "preflight.json"
FREEZE_PATH = TASK_TMP / "freeze.json"
CANARY_PATH = TASK_TMP / "canary-summary.json"
RESERVATION_DIR = TASK_TMP / "reservations"
RECEIPT_DIR = TASK_TMP / "receipts"
SIDECAR_DIR = TASK_TMP / "sidecars"
CANARY_RUN_DIR = TASK_TMP / "canary-runs"
JUDGE_DIR = TASK_TMP / "judge"
LOCK_PATH = TASK_TMP / "operator.lock"
STRUCTURED_PROMPT = "Return exactly a JSON object with verdict PASS and reason 'structured response available'. Do not use tools."
MARKER_PROMPT = "Read marker.txt from your current working directory and put its exact contents in the reason field. If you cannot access it, return INDETERMINATE with a brief reason. Return only the required JSON object."


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_task_dirs() -> None:
    for path in (TASK_TMP, RESERVATION_DIR, RECEIPT_DIR, SIDECAR_DIR, CANARY_RUN_DIR, JUDGE_DIR):
        path.mkdir(parents=True, exist_ok=True)


def candidate_files() -> dict[str, str]:
    """Broader review identity; mutable presentation files are not scientific closure."""
    files = list((REPO_ROOT / "study").rglob("*")) + list((REPO_ROOT / "tests").rglob("*"))
    files += [REPO_ROOT / name for name in (
        "README.md", "docs/RELATED_WORK.md", "docs/SPEC.md", "docs/ARCHITECTURE.md",
        "docs/TRANSPORT_REPAIR_PLAN.md", "docs/PROJECT_LOG.md", "docs/INTERVIEW_GUIDE.md",
        "docs/SPEC_OLLAMA.md", "docs/OLLAMA_ARCHITECTURE.md", "docs/CODEX_OPERABILITY.md",
        "docs/protocols/CODEX_V1.md", "docs/protocols/codex-v1.json",
    )]
    return {p.relative_to(REPO_ROOT).as_posix(): sha256_bytes(p.read_bytes()) for p in sorted(set(files))
            if p.is_file() and "__pycache__" not in p.parts and p.suffix not in {".pyc", ".pyo"}}


def candidate_sha256(hashes: dict[str, str] | None = None) -> str:
    return sha256_bytes(canonical_json(hashes if hashes is not None else candidate_files()))


def ordered_schedule() -> list[dict[str, str]]:
    protocol = load_protocol()
    schedule = []
    for split in ("development", "holdout"):
        for case in load_cases(split):
            conditions = list(protocol["conditions"])
            random.Random(protocol["order_seed"] ^ int(case["case_id"][1:])).shuffle(conditions)
            for condition in conditions:
                prompt = build_prompt(case, condition)
                schedule.append({
                    "split": split, "case_id": case["case_id"], "condition": condition,
                    "prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
                    "code_sha256": sha256_bytes(case["code"].encode("utf-8")),
                    "task_sha256": sha256_bytes(case["task"].encode("utf-8")),
                    "criteria_sha256": sha256_bytes(canonical_json(case["criteria"])),
                    "common_prompt_sha256": sha256_bytes(COMMON_PROMPT.encode("utf-8")),
                })
    return schedule


def _save_json(path: Path, value: Any, create_only: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x" if create_only else "w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")


def _read_json(path: Path) -> dict[str, Any]:
    value = evidence.read_json(path)
    if not isinstance(value, dict):
        raise evidence.EvidenceError("EXPECTED_OBJECT")
    return value


@contextmanager
def _operator_lock():
    ensure_task_dirs()
    with LOCK_PATH.open("x", encoding="utf-8") as stream:
        stream.write(str(os.getpid()))
    try:
        yield
    finally:
        LOCK_PATH.unlink()


def preflight() -> dict[str, Any]:
    ensure_task_dirs()
    os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(TASK_TMP / "tokenizer-cache"))
    try:
        result = validate_protocol()
        cli = codex_cli.inspect_cli()
        login_ok = codex_cli.chatgpt_login_status()
        scientific = evidence.scientific_closure(REPO_ROOT)
        review = candidate_files()
        status = "PASS" if result["status"] == "PASS" and cli["version_check_passed"] and login_ok else "BLOCKED"
        record = {"timestamp_utc": utc_now(), "status": status, "protocol": result, "cli": cli,
                  "auth_route": "chatgpt_subscription" if login_ok else "unavailable",
                  "scientific_files": scientific, "scientific_sha256": evidence.freeze_sha256(scientific),
                  "candidate_files": review, "candidate_sha256": candidate_sha256(review)}
    except Exception as error:
        record = {"timestamp_utc": utc_now(), "status": "BLOCKED", "failure_class": type(error).__name__}
    _save_json(PREFLIGHT_PATH, record)
    return record


def _require_passing_preflight() -> dict[str, Any]:
    record = _read_json(PREFLIGHT_PATH)
    if record.get("status") != "PASS" or record.get("auth_route") != "chatgpt_subscription":
        raise RuntimeError("passing subscription preflight required")
    scientific = evidence.scientific_closure(REPO_ROOT)
    if record.get("scientific_files") != scientific or record.get("scientific_sha256") != evidence.freeze_sha256(scientific):
        raise RuntimeError("scientific source changed after preflight")
    return record


def _records(directory: Path) -> dict[str, dict[str, Any]]:
    if not directory.is_dir():
        raise evidence.EvidenceError("INVENTORY_UNAVAILABLE")
    records = {}
    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.suffix != ".json" or not path.stem.isalnum():
            raise evidence.EvidenceError("INVENTORY_UNEXPECTED_FILE")
        record = _read_json(path)
        if record.get("attempt_id") != path.stem:
            raise evidence.EvidenceError("INVENTORY_ID")
        records[path.stem] = record
    return records


def _inventory() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    reservations, receipts = _records(RESERVATION_DIR), _records(RECEIPT_DIR)
    sidecars = _records(SIDECAR_DIR)
    if set(reservations) != set(receipts) or set(reservations) != set(sidecars):
        raise evidence.EvidenceError("INCOMPLETE_INVENTORY")
    seen_slots = set()
    for attempt, reservation in reservations.items():
        if type(reservation.get("schema_version")) is not int or reservation["schema_version"] != 1 or reservation.get("kind") not in {"study", "canary"}:
            raise evidence.EvidenceError("RESERVATION_SCHEMA")
        if reservation["kind"] == "study":
            if reservation.get("slot_id") in seen_slots:
                raise evidence.EvidenceError("DUPLICATE_STUDY_SLOT")
            seen_slots.add(reservation.get("slot_id"))
            if set(reservation) != evidence.RESERVATION_KEYS:
                raise evidence.EvidenceError("RESERVATION_SCHEMA")
        elif (set(reservation) != {"schema_version", "attempt_id", "slot_id", "kind", "schedule_index", "reserved_utc", "context_sha256"}
              or reservation["schedule_index"] is not None or reservation["slot_id"] not in {"canary:structured", "canary:marker"}):
            raise evidence.EvidenceError("RESERVATION_SCHEMA")
        sidecar_path = SIDECAR_DIR / f"{attempt}.json"
        if receipts[attempt].get("sidecar_sha256") != sha256_bytes(sidecar_path.read_bytes()):
            raise evidence.EvidenceError("SIDECAR_DIGEST")
    return reservations, receipts


def _counts() -> dict[str, int]:
    reservations, _ = _inventory()
    counts = {"canary": 0, "study": 0}
    for reservation in reservations.values():
        counts[reservation["kind"]] += 1
    budget = load_protocol()["turn_budget"]
    if any(counts[kind] > budget[kind] for kind in counts) or sum(counts.values()) > budget["absolute"]:
        raise evidence.EvidenceError("TURN_BUDGET_EXCEEDED")
    return counts


def reserve_call(slot_id: str, kind: str, *, attempt_id: str, context_sha256: str, schedule_index: int | None = None) -> dict[str, Any]:
    counts = _counts()
    budget = load_protocol()["turn_budget"]
    if kind not in counts or counts[kind] >= budget[kind] or sum(counts.values()) >= budget["absolute"]:
        raise RuntimeError("model-turn allowance exhausted or invalid kind")
    if kind == "study" and any(item["slot_id"] == slot_id for item in _records(RESERVATION_DIR).values() if item["kind"] == "study"):
        raise FileExistsError("study cell already reserved")
    reservation = {"schema_version": 1, "attempt_id": attempt_id, "slot_id": slot_id, "kind": kind,
                   "schedule_index": schedule_index, "reserved_utc": utc_now()}
    reservation["freeze_sha256" if kind == "study" else "context_sha256"] = context_sha256
    _save_json(RESERVATION_DIR / f"{attempt_id}.json", reservation, create_only=True)
    return reservation


def _new_judge_directory() -> Path:
    directory = JUDGE_DIR / uuid.uuid4().hex
    directory.mkdir(parents=True, exist_ok=False)
    return codex_cli.validate_working_directory(directory)


def _cleanup_working_directory(directory: Path, marker_path: Path | None = None) -> bool:
    try:
        if marker_path is not None:
            marker_path.unlink(missing_ok=True)
        directory.rmdir()
        return True
    except OSError:
        return False


def _file_digest(path: Path | None) -> str | None:
    if path is None or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(65536):
            digest.update(chunk)
    return digest.hexdigest()


def _execute_reserved_call(
    slot_id: str, call_type: str, prompt: str, prompt_sha256: str, input_hashes: dict[str, str], cli: dict[str, Any],
    *, identity_before: str | None = None, marker: str | None = None, context_sha256: str = "",
    schedule_index: int | None = None, scientific_sha256: str = "", predicate: str | None = None,
) -> dict[str, Any]:
    if sha256_bytes(prompt.encode("utf-8")) != prompt_sha256:
        raise ValueError("prompt digest mismatch before reservation")
    attempt = uuid.uuid4().hex
    reservation = reserve_call(slot_id, call_type, attempt_id=attempt, context_sha256=context_sha256, schedule_index=schedule_index)
    directory = None
    marker_path = None
    entered_transport = False
    result = None
    failed_step, last_step, fault = "create_judge", "reservation_created", None
    cleanup = False
    try:
        directory = _new_judge_directory()
        last_step, failed_step = "judge_created", "stage_marker"
        if marker is not None:
            marker_path = directory / "marker.txt"
            marker_path.write_text(marker, encoding="utf-8")
        last_step, failed_step = "inputs_staged", "dispatch"
        entered_transport = True
        result = codex_cli.run_codex(prompt, directory, load_protocol()["cli"]["timeout_seconds"], marker=marker)
        last_step = result.last_completed_step or "dispatch_returned"
        failed_step, fault = result.failed_step, result.fault_code
    except Exception as error:
        fault = type(error).__name__
    finally:
        if directory is None:
            cleanup = True
        elif not entered_transport or (result is not None and result.cleanup_proven is True):
            try:
                cleanup = _cleanup_working_directory(directory, marker_path)
            except OSError:
                cleanup = False
        if not cleanup and failed_step is None:
            failed_step, fault = "cleanup_judge", "DIRECTORY_NOT_CLEAN"
        if (result is not None and result.reported_model and identity_before and
                result.reported_model != identity_before and failed_step is None):
            failed_step, fault = "backend_identity", "BACKEND_CHANGED"
        if result is None:
            result = codex_cli.ProcessResult("operational_unknown", None, None, None, False, None, 0,
                                              failed_step=failed_step, last_completed_step=last_step, fault_code=fault)
        sidecar = {"attempt_id": attempt, "slot_id": slot_id, "kind": call_type, "context_sha256": context_sha256,
                   "scientific_sha256": scientific_sha256, "prompt_sha256": prompt_sha256, "input_sha256": input_hashes, "cli": cli,
                   "status": result.status, "verdict": result.verdict, "reason": result.reason,
                   "reported_model": result.reported_model, "returncode": result.returncode, "timed_out": result.timed_out,
                   "cleanup_proven": result.cleanup_proven, "forced_cleanup": result.forced_cleanup,
                   "active_processes_final": result.active_processes_final, "judge_directory_cleaned": cleanup,
                   "failed_step": failed_step, "last_completed_step": last_step, "fault_code": fault,
                   "tool_event": result.tool_event, "marker_echo": result.marker_echo, "marker": marker,
                   "protocol_violations": list(result.protocol_violations)}
        capture_fault = None
        for name in ("stdout", "stderr", "terminal", "metadata"):
            path = getattr(result, f"{name}_path")
            sidecar[f"{name}_path"] = str(path) if path else None
            try:
                sidecar[f"{name}_sha256"] = _file_digest(path)
            except OSError as error:
                capture_fault = type(error).__name__
                sidecar[f"{name}_sha256"] = None
        if capture_fault:
            sidecar["failed_step"], sidecar["fault_code"] = "capture_digest", capture_fault
        for name in ("stdout", "stderr"):
            capture = getattr(result, f"{name}_capture")
            sidecar[f"{name}_bytes"] = capture.byte_count if capture else None
            sidecar[f"{name}_head_hex"] = capture.head.hex() if capture else None
            sidecar[f"{name}_tail_hex"] = capture.tail.hex() if capture else None
            sidecar[f"{name}_truncated"] = capture.truncated if capture else None
        sidecar_path = SIDECAR_DIR / f"{attempt}.json"
        _save_json(sidecar_path, sidecar, create_only=True)
        sidecar_hash = sha256_bytes(sidecar_path.read_bytes())
        clean = (not capture_fault and cleanup and result.cleanup_proven is True and result.forced_cleanup is False
                 and type(result.active_processes_final) is int and result.active_processes_final == 0 and result.returncode == 0
                 and result.timed_out is False and (not identity_before or not result.reported_model or result.reported_model == identity_before))
        if call_type == "canary":
            receipt = {"attempt_id": attempt, "predicate": predicate, "context_sha256": context_sha256,
                       "sidecar_sha256": sidecar_hash, "status": result.status if clean else "operational_unknown",
                       "verdict": result.verdict if clean and result.status == "valid" else None, "reason": result.reason if clean and result.status == "valid" else None,
                       "tool_event": result.tool_event, "marker_echo": result.marker_echo,
                       "cleanup_proven": result.cleanup_proven, "forced_cleanup": result.forced_cleanup,
                       "active_processes_final": result.active_processes_final, "judge_directory_cleaned": cleanup}
        else:
            receipt = {**reservation, "sidecar_sha256": sidecar_hash, "scientific_sha256": scientific_sha256, "cli": cli,
                       "requested_model": load_protocol()["model"]["requested_alias"], "reasoning_effort": load_protocol()["model"]["reasoning_effort"],
                       "input_sha256": input_hashes, "timestamp_utc": utc_now(), "status": result.status if clean else "operational_unknown",
                       "verdict": result.verdict if clean and result.status == "valid" else None, "reason": result.reason if clean and result.status == "valid" else None,
                       "reported_model": result.reported_model, "terminal_exit": result.returncode, "timed_out": result.timed_out,
                       "cleanup_proven": result.cleanup_proven, "forced_cleanup": result.forced_cleanup,
                       "active_processes_final": result.active_processes_final, "judge_directory_cleaned": cleanup,
                       "stdout_sha256": sidecar["stdout_sha256"], "stderr_sha256": sidecar["stderr_sha256"],
                       "stdout_bytes": sidecar["stdout_bytes"], "stderr_bytes": sidecar["stderr_bytes"]}
        _save_json(RECEIPT_DIR / f"{attempt}.json", receipt, create_only=True)
    return receipt




def _private_path(path: Any, root: Path) -> Path:
    if not isinstance(path, str):
        raise evidence.EvidenceError("PRIVATE_CAPTURE_MISSING")
    resolved = Path(path).resolve()
    if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
        raise evidence.EvidenceError("PRIVATE_CAPTURE_PATH")
    return resolved


def _verify_sidecar(root: Path, receipt: dict[str, Any], reservation: dict[str, Any], context: dict[str, Any] | None = None) -> dict[str, Any]:
    attempt = receipt["attempt_id"]
    sidecar_path = root / "sidecars" / f"{attempt}.json"
    if _file_digest(sidecar_path) != receipt.get("sidecar_sha256"):
        raise evidence.EvidenceError("SIDECAR_DIGEST")
    sidecar = _read_json(sidecar_path)
    if sidecar.get("attempt_id") != attempt or sidecar.get("slot_id") != reservation.get("slot_id") or sidecar.get("kind") != reservation.get("kind"):
        raise evidence.EvidenceError("SIDECAR_RESERVATION")
    expected_context = reservation.get("freeze_sha256", reservation.get("context_sha256"))
    if sidecar.get("context_sha256") != expected_context:
        raise evidence.EvidenceError("SIDECAR_CONTEXT")
    if reservation["kind"] == "study" and (
            sidecar.get("scientific_sha256") != receipt.get("scientific_sha256") or sidecar.get("cli") != receipt.get("cli") or
            sidecar.get("input_sha256") != receipt.get("input_sha256") or
            sidecar.get("prompt_sha256") != receipt.get("input_sha256", {}).get("prompt")):
        raise evidence.EvidenceError("SIDECAR_INPUT_IDENTITY")
    for receipt_key, sidecar_key in (("terminal_exit", "returncode"), ("timed_out", "timed_out"),
                                     ("cleanup_proven", "cleanup_proven"), ("forced_cleanup", "forced_cleanup"),
                                     ("active_processes_final", "active_processes_final"), ("judge_directory_cleaned", "judge_directory_cleaned"),
                                     ("reported_model", "reported_model")):
        if receipt_key in receipt and receipt[receipt_key] != sidecar.get(sidecar_key):
            raise evidence.EvidenceError("SIDECAR_FACTS")
    for name in ("stdout", "stderr", "terminal", "metadata"):
        path_value = sidecar.get(f"{name}_path")
        if path_value is None:
            if receipt.get("status") == "valid":
                raise evidence.EvidenceError("VALID_CAPTURE_MISSING")
            continue
        path = _private_path(path_value, root)
        if _file_digest(path) != sidecar.get(f"{name}_sha256"):
            raise evidence.EvidenceError("SIDECAR_CAPTURE_DIGEST")
        if name in {"stdout", "stderr"}:
            if path.stat().st_size != sidecar.get(f"{name}_bytes"):
                raise evidence.EvidenceError("SIDECAR_CAPTURE_SIZE")
            if f"{name}_sha256" in receipt and (receipt[f"{name}_sha256"] != sidecar[f"{name}_sha256"] or receipt[f"{name}_bytes"] != sidecar[f"{name}_bytes"]):
                raise evidence.EvidenceError("SIDECAR_CAPTURE_JOIN")
    if receipt.get("status") == "valid":
        terminal = _read_json(_private_path(sidecar["terminal_path"], root))
        metadata = _read_json(_private_path(sidecar["metadata_path"], root))
        if type(terminal.get("returncode")) is not int or terminal["returncode"] != 0 or terminal.get("failed_step") is not None or terminal.get("fault_code") is not None:
            raise evidence.EvidenceError("TERMINAL_RECORD")
        if not all(type(metadata.get(key)) is int and metadata[key] > 0 for key in ("wrapper_pid", "cli_pid")):
            raise evidence.EvidenceError("PROCESS_METADATA")
        if sidecar.get("status") != "valid" or sidecar.get("verdict") != receipt.get("verdict") or sidecar.get("reason") != receipt.get("reason"):
            raise evidence.EvidenceError("SIDECAR_CLASSIFICATION")
    if context is not None:
        name = receipt["predicate"]
        if sidecar.get("scientific_sha256") != context["scientific_sha256"] or sidecar.get("cli") != context["cli"] or sidecar.get("prompt_sha256") != context["predicates"][name]["prompt_sha256"]:
            raise evidence.EvidenceError("CANARY_INPUT_IDENTITY")
        marker = sidecar.get("marker")
        if name == "marker" and (not isinstance(marker, str) or sha256_bytes(marker.encode("utf-8")) != context["predicates"][name]["marker_sha256"]):
            raise evidence.EvidenceError("CANARY_MARKER_IDENTITY")
        marker_bytes = marker.encode("utf-8") if marker else None
        _, stdout, stdout_echo = codex_cli._capture(_private_path(sidecar["stdout_path"], root), marker_bytes, True)
        _, _, stderr_echo = codex_cli._capture(_private_path(sidecar["stderr_path"], root), marker_bytes, False)
        if stdout_echo or stderr_echo:
            raise evidence.EvidenceError("CANARY_MARKER_ECHO")
        if stdout is None:
            raise evidence.EvidenceError("CANARY_STDOUT_OVERSIZED")
        parsed = codex_cli.parse_event_stream(stdout.decode("utf-8"), sidecar["returncode"], sidecar["timed_out"])
        if (parsed.status, parsed.verdict, parsed.reason, parsed.tool_event, parsed.reported_model) != (receipt["status"], receipt["verdict"], receipt["reason"], False, sidecar["reported_model"]):
            raise evidence.EvidenceError("CANARY_RAW_REPLAY")
    return sidecar


def _canary_context(cli: dict[str, Any], marker: str) -> dict[str, Any]:
    protocol = load_protocol()
    return {"scientific_sha256": evidence.freeze_sha256(evidence.scientific_closure(REPO_ROOT)), "cli": cli,
            "requested_model": protocol["model"]["requested_alias"], "reasoning_effort": protocol["model"]["reasoning_effort"],
            "predicates": {"structured": {"prompt_sha256": sha256_bytes(STRUCTURED_PROMPT.encode()),
                                          "verdict": "PASS", "reason": "structured response available"},
                           "marker": {"prompt_sha256": sha256_bytes(MARKER_PROMPT.encode()),
                                      "marker_sha256": sha256_bytes(marker.encode()), "verdict": "INDETERMINATE"}}}


def _verified_admission(root: Path, expected_cli: dict[str, Any], expected_science: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Path]]:
    record = _read_json(root / "canary-summary.json")
    if set(record) != {"admission", "context", "attempts"}:
        raise evidence.EvidenceError("ADMISSION_SUMMARY_SCHEMA")
    admission, context, attempts = record["admission"], record["context"], record["attempts"]
    if context["scientific_sha256"] != expected_science or context["cli"] != expected_cli:
        raise evidence.EvidenceError("ADMISSION_IDENTITY_CHANGED")
    if (context["predicates"]["structured"]["prompt_sha256"] != sha256_bytes(STRUCTURED_PROMPT.encode()) or
            context["predicates"]["marker"]["prompt_sha256"] != sha256_bytes(MARKER_PROMPT.encode())):
        raise evidence.EvidenceError("ADMISSION_PROMPT_CHANGED")
    paths = {name: root / "receipts" / f"{attempts[name]}.json" for name in ("structured", "marker")}
    def verify(name: str, receipt: dict[str, Any]) -> bool:
        reservation = _read_json(root / "reservations" / f"{receipt['attempt_id']}.json")
        if reservation.get("kind") != "canary" or reservation.get("context_sha256") != evidence.freeze_sha256(context) or reservation.get("slot_id") != f"canary:{name}":
            raise evidence.EvidenceError("CANARY_RESERVATION")
        _verify_sidecar(root, receipt, reservation, context)
        return True
    evidence.verify_admission(admission, context, paths, verify)
    return admission, context, paths


def run_canaries(authorize: bool, gates_confirmed: bool, changed_premise: str | None = None) -> dict[str, Any]:
    if not authorize or not gates_confirmed:
        raise RuntimeError("canaries require explicit subscription-call authorization and confirmed offline review/QA")
    with _operator_lock():
        if FREEZE_PATH.exists():
            raise RuntimeError("canaries cannot run after freeze")
        preflight_result = _require_passing_preflight()
        cli = codex_cli.inspect_cli()
        if cli != preflight_result["cli"] or not codex_cli.chatgpt_login_status():
            raise RuntimeError("CLI identity or subscription route changed")
        counts = _counts()
        if counts["study"]:
            raise evidence.EvidenceError("STUDY_RESERVED_BEFORE_FREEZE")
        if CANARY_PATH.exists():
            admission, _, _ = _verified_admission(TASK_TMP, cli, preflight_result["scientific_sha256"])
            return {"status": "PASS", "admission": admission}
        prior = []
        for path in sorted(CANARY_RUN_DIR.iterdir()):
            if not path.is_file() or path.suffix != ".json":
                raise evidence.EvidenceError("CANARY_RUN_INVENTORY")
            previous = _read_json(path)
            if set(previous) != {"run_id", "timestamp_utc", "status", "scientific_sha256", "cli", "changed_premise", "attempts"}:
                raise evidence.EvidenceError("CANARY_RUN_SCHEMA")
            prior.append(previous)
        if prior:
            prior.sort(key=lambda item: item["timestamp_utc"])
            latest = prior[-1]
            if not isinstance(changed_premise, str) or not changed_premise.strip():
                raise RuntimeError("explicit changed-premise reason required")
            if latest["scientific_sha256"] == preflight_result["scientific_sha256"] and latest["cli"] == cli:
                raise RuntimeError("unchanged scientific source and CLI/configuration cannot be readmitted")
        budget = load_protocol()["turn_budget"]
        if counts["canary"] + 2 > budget["canary"] or sum(counts.values()) + 2 > budget["absolute"]:
            raise RuntimeError("insufficient allowance for both canary predicates")
        marker = "STUDY-CANARY-" + secrets.token_hex(16)
        context = _canary_context(cli, marker)
        context_hash = evidence.freeze_sha256(context)
        run_id = uuid.uuid4().hex
        summary = {"run_id": run_id, "timestamp_utc": utc_now(), "status": "BLOCKED",
                   "scientific_sha256": context["scientific_sha256"], "cli": cli,
                   "changed_premise": changed_premise, "attempts": {}}
        try:
            for name, prompt, private_marker in (("structured", STRUCTURED_PROMPT, None), ("marker", MARKER_PROMPT, marker)):
                receipt = _execute_reserved_call(f"canary:{name}", "canary", prompt, sha256_bytes(prompt.encode()),
                                                 {"prompt": sha256_bytes(prompt.encode())}, cli, marker=private_marker,
                                                 context_sha256=context_hash, scientific_sha256=context["scientific_sha256"], predicate=name)
                summary["attempts"][name] = receipt["attempt_id"]
                expected = context["predicates"][name]
                if (receipt["status"] != "valid" or receipt["verdict"] != expected["verdict"] or
                        (name == "structured" and receipt["reason"] != expected["reason"]) or
                        receipt["tool_event"] is not False or receipt["marker_echo"] is not False):
                    return {"status": "BLOCKED", "failure_status": "CANARY_PREDICATE", "attempts": summary["attempts"]}
            paths = {name: RECEIPT_DIR / f"{attempt}.json" for name, attempt in summary["attempts"].items()}
            admission = {"schema_version": 1, "status": "PASS", "admitted_utc": utc_now(), "scientific_sha256": context["scientific_sha256"],
                         "cli": cli, "context_sha256": context_hash,
                         "receipt_sha256": {name: _file_digest(path) for name, path in paths.items()}}
            def verify(name: str, receipt: dict[str, Any]) -> bool:
                reservation = _read_json(RESERVATION_DIR / f"{receipt['attempt_id']}.json")
                _verify_sidecar(TASK_TMP, receipt, reservation, context)
                return True
            evidence.verify_admission(admission, context, paths, verify)
            _save_json(CANARY_PATH, {"admission": admission, "context": context, "attempts": summary["attempts"]}, create_only=True)
            summary["status"] = "PASS"
            return {"status": "PASS", "admission": admission}
        finally:
            _save_json(CANARY_RUN_DIR / f"{run_id}.json", summary, create_only=True)


def freeze_protocol() -> dict[str, Any]:
    with _operator_lock():
        preflight_result = _require_passing_preflight()
        if _counts()["study"]:
            raise evidence.EvidenceError("STUDY_RESERVED_BEFORE_FREEZE")
        if FREEZE_PATH.exists():
            raise FileExistsError("freeze already exists")
        cli = codex_cli.inspect_cli()
        if cli != preflight_result["cli"] or not codex_cli.chatgpt_login_status():
            raise RuntimeError("CLI identity or subscription route changed")
        admission, context, paths = _verified_admission(TASK_TMP, cli, preflight_result["scientific_sha256"])
        scientific = evidence.scientific_closure(REPO_ROOT)
        protocol, schedule = load_protocol(), ordered_schedule()
        frozen = {"schema_version": 1, "frozen_utc": utc_now(), "scientific_files": scientific, "scientific_sha256": evidence.freeze_sha256(scientific),
                  "protocol": protocol, "schedule": schedule, "cli": cli, "auth_route": "chatgpt_subscription", "admission": admission}
        freeze_hash = evidence.freeze_sha256(frozen)
        evidence.verify_freeze(frozen, freeze_hash, scientific_files=scientific, protocol=protocol, schedule=schedule, cli=cli,
                               admission=admission, admission_context=context, admission_receipt_paths=paths,
                               verify_admission_receipt=lambda name, receipt: bool(_verify_sidecar(TASK_TMP, receipt,
                                   _read_json(RESERVATION_DIR / f"{receipt['attempt_id']}.json"), context)))
        _save_json(FREEZE_PATH, frozen, create_only=True)
        return {"status": "PASS", "freeze_sha256": freeze_hash, "study_turns": len(schedule)}


def load_private_bundle(root: Path = TASK_TMP) -> dict[str, Any]:
    """Verify the offline private bundle without inspecting CLI or credentials."""
    root = Path(root).resolve()
    frozen = _read_json(root / "freeze.json")
    freeze_hash = evidence.freeze_sha256(frozen)
    scientific = evidence.scientific_closure(REPO_ROOT)
    if frozen["cli"]["configuration_sha256"] != codex_cli.configuration_sha256():
        raise evidence.EvidenceError("CONFIGURATION_CHANGED")
    admission, context, paths = _verified_admission(root, frozen["cli"], evidence.freeze_sha256(scientific))
    def verify(name: str, receipt: dict[str, Any]) -> bool:
        reservation = _read_json(root / "reservations" / f"{receipt['attempt_id']}.json")
        _verify_sidecar(root, receipt, reservation, context)
        return True
    evidence.verify_freeze(frozen, freeze_hash, scientific_files=scientific, protocol=load_protocol(), schedule=ordered_schedule(),
                           cli=frozen["cli"], admission=admission, admission_context=context,
                           admission_receipt_paths=paths, verify_admission_receipt=verify)
    reservations = _records(root / "reservations")
    receipts = _records(root / "receipts")
    sidecars = _records(root / "sidecars")
    if set(reservations) != set(receipts) or set(reservations) != set(sidecars):
        raise evidence.EvidenceError("INCOMPLETE_INVENTORY")
    budget = load_protocol()["turn_budget"]
    counts = {"canary": 0, "study": 0}
    for attempt, reservation in reservations.items():
        kind = reservation.get("kind")
        if kind not in counts:
            raise evidence.EvidenceError("RESERVATION_KIND")
        if kind == "canary" and (
                set(reservation) != {"schema_version", "attempt_id", "slot_id", "kind", "schedule_index", "reserved_utc", "context_sha256"}
                or type(reservation["schema_version"]) is not int or reservation["schema_version"] != 1 or
                reservation["schedule_index"] is not None or reservation["slot_id"] not in {"canary:structured", "canary:marker"}):
            raise evidence.EvidenceError("RESERVATION_SCHEMA")
        counts[kind] += 1
        if counts[kind] > budget[kind] or sum(counts.values()) > budget["absolute"]:
            raise evidence.EvidenceError("TURN_BUDGET_EXCEEDED")
        _verify_sidecar(root, receipts[attempt], reservation)
    study_reservations = sorted((item for item in reservations.values() if item["kind"] == "study"), key=lambda item: item["schedule_index"])
    study_receipts = [receipts[item["attempt_id"]] for item in study_reservations]
    evidence.verify_inventory(frozen, study_reservations, study_receipts, freeze_hash)
    for reservation, receipt in zip(study_reservations, study_receipts):
        sidecar = _verify_sidecar(root, receipt, reservation)
        evidence.verify_private_receipt(frozen, freeze_hash, reservation, receipt,
                                        _private_path(sidecar["stdout_path"], root), _private_path(sidecar["stderr_path"], root),
                                        codex_cli.parse_event_stream)
    return {"verification_scope": "private_raw_verified", "freeze": frozen, "freeze_sha256": freeze_hash,
            "reservations": study_reservations, "receipts": study_receipts, "canary_reservations": counts["canary"],
            "canary_ledger": [item for item in reservations.values() if item["kind"] == "canary"]}


def _load_verified_freeze() -> dict[str, Any]:
    return load_private_bundle(TASK_TMP)["freeze"]


def run_split(split: str, authorize: bool) -> dict[str, Any]:
    if split not in {"development", "holdout"}:
        raise ValueError("split must be development or holdout")
    if not authorize:
        raise RuntimeError("study calls require --authorize-subscription-calls")
    with _operator_lock():
        preflight_result = _require_passing_preflight()
        bundle = load_private_bundle(TASK_TMP)
        frozen = bundle["freeze"]
        if codex_cli.inspect_cli() != frozen["cli"] or preflight_result["cli"] != frozen["cli"] or not codex_cli.chatgpt_login_status():
            raise RuntimeError("CLI identity or subscription route changed")
        receipts = bundle["receipts"]
        if receipts and receipts[-1]["status"] != "valid":
            return {"status": "BLOCKED", "failure_status": receipts[-1]["status"], "new_attempts": 0}
        prior_identity = next((item["reported_model"] for item in receipts if item["reported_model"]), None)
        schedule = frozen["schedule"]
        start = len(receipts)
        if start < len(schedule) and schedule[start]["split"] != split:
            raise RuntimeError("requested split is not the next frozen schedule prefix")
        cases = {case["case_id"]: case for case in load_cases(split)}
        attempted = 0
        for index in range(start, len(schedule)):
            cell = schedule[index]
            if cell["split"] != split:
                break
            if codex_cli.inspect_cli() != frozen["cli"]:
                raise RuntimeError("CLI identity changed during run")
            prompt = build_prompt(cases[cell["case_id"]], cell["condition"])
            hashes = {key: cell[f"{key}_sha256"] for key in ("code", "task", "criteria", "common_prompt", "prompt")}
            slot = f"study:{split}:{cell['case_id']}:{cell['condition']}"
            receipt = _execute_reserved_call(slot, "study", prompt, hashes["prompt"], hashes, frozen["cli"],
                                             identity_before=prior_identity, context_sha256=bundle["freeze_sha256"],
                                             schedule_index=index, scientific_sha256=frozen["scientific_sha256"])
            attempted += 1
            if receipt["status"] != "valid":
                return {"status": "BLOCKED", "failure_status": receipt["status"], "new_attempts": attempted, "stopped_at": slot}
            bundle = load_private_bundle(TASK_TMP)
            if receipt["reported_model"]:
                prior_identity = receipt["reported_model"]
        return {"status": "PASS", "split": split, "new_attempts": attempted,
                "valid_existing_calls": start, "total_reserved": _counts()}


# Preserve the separately archived v1 route for legacy replay and fixtures.
_preflight_v1 = preflight
_require_passing_preflight_v1 = _require_passing_preflight
_execute_reserved_call_v1 = _execute_reserved_call
_verified_admission_v1 = _verified_admission
_run_canaries_v1 = run_canaries
_freeze_protocol_v1 = freeze_protocol
_load_private_bundle_v1 = load_private_bundle
_run_split_v1 = run_split


def _v2_active() -> bool:
    return load_protocol().get("schema_version") == 2


def _transport_identity(runtime: dict[str, Any]) -> dict[str, Any]:
    return {"configuration_sha256": ollama.configuration_sha256(),
            "runtime_identity_sha256": evidence.freeze_sha256(runtime), "runtime_identity": runtime}


def preflight() -> dict[str, Any]:
    if not _v2_active():
        return _preflight_v1()
    ensure_task_dirs()
    os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(TASK_TMP / "tokenizer-cache"))
    try:
        historical = history.ensure_history(TASK_TMP)
        result = validate_protocol()
        runtime = ollama.inspect_runtime()
        transport = _transport_identity(runtime)
        scientific = evidence.scientific_closure(REPO_ROOT)
        review = candidate_files()
        record = {"schema_version": 2, "provider": "ollama_local", "timestamp_utc": utc_now(),
                  "status": "PASS" if result["status"] == "PASS" else "BLOCKED", "protocol": result,
                  "transport": transport, "auth_route": "local_unauthenticated", "history_sha256": historical["sha256"],
                  "scientific_files": scientific, "scientific_sha256": evidence.freeze_sha256(scientific),
                  "candidate_files": review, "candidate_sha256": candidate_sha256(review)}
    except Exception as error:
        record = {"schema_version": 2, "provider": "ollama_local", "timestamp_utc": utc_now(),
                  "status": "BLOCKED", "failure_class": type(error).__name__}
    _save_json(PREFLIGHT_PATH, record)
    return record


def _require_passing_preflight() -> dict[str, Any]:
    if not _v2_active():
        return _require_passing_preflight_v1()
    record = _read_json(PREFLIGHT_PATH)
    scientific = evidence.scientific_closure(REPO_ROOT)
    historical = history.verify_history(TASK_TMP)
    if (record.get("schema_version") != 2 or record.get("provider") != "ollama_local" or
            record.get("status") != "PASS" or record.get("auth_route") != "local_unauthenticated" or
            record.get("scientific_files") != scientific or record.get("scientific_sha256") != evidence.freeze_sha256(scientific) or
            record.get("history_sha256") != historical["sha256"] or
            record.get("transport", {}).get("configuration_sha256") != ollama.configuration_sha256()):
        raise RuntimeError("passing unchanged v2 preflight required")
    return record


def _v2_context(transport: dict[str, Any], marker: str, historical_sha256: str) -> dict[str, Any]:
    predicates = {}
    for name, prompt in (("structured", STRUCTURED_PROMPT), ("marker", MARKER_PROMPT)):
        request = ollama.build_request(prompt)
        predicates[name] = {"prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
                            "request_sha256": sha256_bytes(request), "request_bytes": len(request),
                            "verdict": "PASS" if name == "structured" else "INDETERMINATE"}
    predicates["structured"]["reason"] = "structured response available"
    predicates["marker"]["marker_sha256"] = sha256_bytes(marker.encode("utf-8"))
    return {"schema_version": 2, "provider": "ollama_local", "scientific_sha256": evidence.freeze_sha256(evidence.scientific_closure(REPO_ROOT)),
            "transport": transport, "history_sha256": historical_sha256, "predicates": predicates}


def _execute_reserved_call(
    slot_id: str, call_type: str, prompt: str, prompt_sha256: str, input_hashes: dict[str, str], cli: dict[str, Any],
    *, identity_before: str | None = None, marker: str | None = None, context_sha256: str = "",
    schedule_index: int | None = None, scientific_sha256: str = "", predicate: str | None = None,
    history_sha256: str = "",
) -> dict[str, Any]:
    if not _v2_active():
        return _execute_reserved_call_v1(slot_id, call_type, prompt, prompt_sha256, input_hashes, cli,
                                         identity_before=identity_before, marker=marker, context_sha256=context_sha256,
                                         schedule_index=schedule_index, scientific_sha256=scientific_sha256, predicate=predicate)
    if sha256_bytes(prompt.encode("utf-8")) != prompt_sha256:
        raise ValueError("prompt digest mismatch before reservation")
    request = ollama.build_request(prompt)
    attempt = uuid.uuid4().hex
    reservation = reserve_call(slot_id, call_type, attempt_id=attempt, context_sha256=context_sha256, schedule_index=schedule_index)
    reservation_hash = _file_digest(RESERVATION_DIR / f"{attempt}.json")
    directory = marker_path = result = runtime_before = runtime_after = None
    failed_step, last_step, fault = "create_judge", "reservation_created", None
    cleanup = entered_transport = False
    try:
        directory = _new_judge_directory()
        last_step, failed_step = "judge_created", "stage_marker"
        if marker is not None:
            marker_path = directory / "marker.txt"
            marker_path.write_text(marker, encoding="utf-8")
        last_step, failed_step = "inputs_staged", "runtime_before"
        runtime_before = ollama.inspect_runtime()
        if runtime_before != cli["runtime_identity"]:
            raise ValueError("runtime identity changed before dispatch")
        last_step, failed_step = "runtime_verified", "dispatch"
        entered_transport = True
        result = ollama.run_ollama(prompt, directory, load_protocol()["transport"]["timeout_seconds"], marker=marker)
        last_step = result.last_completed_step or "dispatch_returned"
        failed_step, fault = result.failed_step, result.fault_code
        if result.timed_out is False:
            failed_step = failed_step or "runtime_after"
            runtime_after = ollama.inspect_runtime()
            if runtime_after != cli["runtime_identity"]:
                raise ValueError("runtime identity changed after dispatch")
            if failed_step == "runtime_after":
                failed_step = None
    except Exception as error:
        fault = type(error).__name__
    finally:
        if directory is None:
            cleanup = True
        elif not entered_transport or (result is not None and result.cleanup_proven is True):
            cleanup = _cleanup_working_directory(directory, marker_path)
        if not cleanup and failed_step is None:
            failed_step, fault = "cleanup_judge", "DIRECTORY_NOT_CLEAN"
        if result is None:
            result = ollama.OllamaResult("operational_unknown", None, None, None, False, None, 0,
                                         failed_step=failed_step, last_completed_step=last_step, fault_code=fault)
        clean = (failed_step is None and runtime_before == runtime_after == cli["runtime_identity"] and cleanup and
                 result.cleanup_proven is True and result.forced_cleanup is False and result.active_processes_final == 0 and
                 type(result.active_processes_final) is int and result.returncode == 0 and result.timed_out is False and
                 result.request_sha256 == sha256_bytes(request) and result.request_bytes == len(request))
        status = result.status if clean else "operational_unknown"
        verdict = result.verdict if status == "valid" else None
        reason = result.reason if status == "valid" else None
        sidecar = {"schema_version": 2, "provider": "ollama_local", "attempt_id": attempt, "slot_id": slot_id,
                   "context_sha256": context_sha256, "scientific_sha256": scientific_sha256, "transport": cli,
                   "history_sha256": history_sha256, "prompt_sha256": prompt_sha256, "input_sha256": input_hashes,
                   "request_sha256": sha256_bytes(request), "request_bytes": len(request),
                   "runtime_before": runtime_before, "runtime_after": runtime_after,
                   "status": status, "verdict": verdict, "reason": reason, "reported_model": result.reported_model,
                   "terminal_exit": result.returncode, "timed_out": result.timed_out, "cleanup_proven": result.cleanup_proven,
                   "forced_cleanup": result.forced_cleanup, "active_processes_final": result.active_processes_final,
                   "judge_directory_cleaned": cleanup, "failed_step": failed_step, "last_completed_step": last_step,
                   "fault_code": fault, "native_failed_step": (result.transport_facts or {}).get("native_failed_step"), "marker_echo": result.marker_echo,
                   "tool_event": result.tool_event, "protocol_violations": list(result.protocol_violations), "marker": marker}
        for name in ("stdout", "stderr", "terminal", "metadata", "http_metadata"):
            path = getattr(result, f"{name}_path", None)
            sidecar[f"{name}_path"] = str(path) if path else None
            try:
                digest = _file_digest(path)
            except OSError:
                digest = None
            sidecar["transport_metadata_sha256" if name == "http_metadata" else f"{name}_sha256"] = digest
        for name in ("stdout", "stderr"):
            capture = getattr(result, f"{name}_capture")
            sidecar[f"{name}_bytes"] = capture.byte_count if capture else None
            sidecar[f"{name}_head_hex"] = capture.head.hex() if capture else None
            sidecar[f"{name}_tail_hex"] = capture.tail.hex() if capture else None
            sidecar[f"{name}_truncated"] = capture.truncated if capture else None
        if status != "operational_unknown" and (any(sidecar[key] is None for key in (
                "stdout_sha256", "stderr_sha256", "terminal_sha256", "metadata_sha256", "transport_metadata_sha256",
                "stdout_bytes", "stderr_bytes"))):
            status, verdict, reason = "operational_unknown", None, None
            sidecar.update(status=status, verdict=None, reason=None, failed_step="capture_digest", fault_code="CAPTURE_MISSING")
        sidecar_path = SIDECAR_DIR / f"{attempt}.json"
        _save_json(sidecar_path, sidecar, create_only=True)
        common = {"schema_version": 2, "provider": "ollama_local", "attempt_id": attempt,
                  "reservation_sha256": reservation_hash, "sidecar_sha256": _file_digest(sidecar_path),
                  "transport_metadata_sha256": sidecar["transport_metadata_sha256"], "request_sha256": sidecar["request_sha256"],
                  "request_bytes": len(request), "status": status, "verdict": verdict, "reason": reason,
                  "reported_model": result.reported_model, "marker_echo": result.marker_echo,
                  "cleanup_proven": result.cleanup_proven, "forced_cleanup": result.forced_cleanup,
                  "active_processes_final": result.active_processes_final, "judge_directory_cleaned": cleanup}
        if call_type == "canary":
            receipt = {**common, "predicate": predicate, "context_sha256": context_sha256, "tool_event": result.tool_event,
                       "runtime_before_sha256": evidence.freeze_sha256(runtime_before) if runtime_before else None,
                       "runtime_after_sha256": evidence.freeze_sha256(runtime_after) if runtime_after else None}
        else:
            receipt = {**reservation, **common, "scientific_sha256": scientific_sha256, "transport": cli,
                       "history_sha256": history_sha256, "input_sha256": input_hashes, "timestamp_utc": utc_now(),
                       "terminal_exit": result.returncode, "timed_out": result.timed_out, "native_failed_step": sidecar["native_failed_step"],
                       "runtime_before_sha256": evidence.freeze_sha256(runtime_before) if runtime_before else None,
                       "runtime_after_sha256": evidence.freeze_sha256(runtime_after) if runtime_after else None,
                       "stdout_sha256": sidecar["stdout_sha256"], "stderr_sha256": sidecar["stderr_sha256"],
                       "stdout_bytes": sidecar["stdout_bytes"], "stderr_bytes": sidecar["stderr_bytes"]}
        _save_json(RECEIPT_DIR / f"{attempt}.json", receipt, create_only=True)
    return receipt


def _v2_verify_canary(root: Path, context: dict[str, Any], name: str, receipt: dict[str, Any]) -> bool:
    attempt = receipt["attempt_id"]
    prompt = STRUCTURED_PROMPT if name == "structured" else MARKER_PROMPT
    if context["predicates"][name]["prompt_sha256"] != sha256_bytes(prompt.encode("utf-8")):
        raise evidence.EvidenceError("V2_CANARY_PROMPT")
    evidence.verify_v2_private_canary(context, root / "reservations" / f"{attempt}.json",
                                     root / "receipts" / f"{attempt}.json", root / "sidecars" / f"{attempt}.json",
                                     root, ollama.build_request(prompt), ollama.parse_response)
    return True


def _v2_canary_history(root: Path, historical: dict[str, Any], reservations: dict[str, dict[str, Any]],
                       receipts: dict[str, dict[str, Any]]) -> None:
    historical_ids = {item["attempt_id"] for item in historical["manifest"]["attempts"]}
    if not historical_ids <= set(reservations):
        raise evidence.EvidenceError("HISTORY_MISSING")
    canary_runs: dict[str, tuple[dict[str, Any], str]] = {}
    for path in sorted((root / "canary-runs").glob("*.json")):
        run = _read_json(path)
        if run.get("provider") != "ollama_local":
            continue
        context = run["context"]
        if context["history_sha256"] != historical["sha256"]:
            raise evidence.EvidenceError("CANARY_HISTORY")
        for name, attempt in run["attempts"].items():
            if name not in {"structured", "marker"} or attempt in canary_runs:
                raise evidence.EvidenceError("CANARY_RUN_INVENTORY")
            canary_runs[attempt] = (context, name)
    expected = {attempt for attempt, item in reservations.items() if item.get("kind") == "canary" and attempt not in historical_ids}
    if set(canary_runs) != expected:
        raise evidence.EvidenceError("CANARY_RUN_INVENTORY")
    for attempt, (context, name) in canary_runs.items():
        _v2_verify_canary(root, context, name, receipts[attempt])


def _verified_admission(root: Path, expected_cli: dict[str, Any], expected_science: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Path]]:
    if not _v2_active():
        return _verified_admission_v1(root, expected_cli, expected_science)
    record = _read_json(root / "canary-summary.json")
    if set(record) != {"admission", "context", "attempts"}:
        raise evidence.EvidenceError("ADMISSION_SUMMARY_SCHEMA")
    admission, context, attempts = record["admission"], record["context"], record["attempts"]
    if context.get("transport") != expected_cli or context.get("scientific_sha256") != expected_science:
        raise evidence.EvidenceError("ADMISSION_IDENTITY_CHANGED")
    paths = {name: root / "receipts" / f"{attempts[name]}.json" for name in ("structured", "marker")}
    evidence.verify_v2_admission(admission, context, paths, lambda name, receipt: _v2_verify_canary(root, context, name, receipt))
    return admission, context, paths


def run_canaries(authorize: bool, gates_confirmed: bool, changed_premise: str | None = None) -> dict[str, Any]:
    if not _v2_active():
        return _run_canaries_v1(authorize, gates_confirmed, changed_premise)
    if not authorize or not gates_confirmed:
        raise RuntimeError("canaries require explicit local-call authorization and confirmed offline review/QA")
    with _operator_lock():
        if FREEZE_PATH.exists():
            raise RuntimeError("canaries cannot run after freeze")
        preflight_result = _require_passing_preflight()
        transport = _transport_identity(ollama.inspect_runtime())
        if transport != preflight_result["transport"]:
            raise RuntimeError("runtime identity changed")
        counts = _counts()
        reservations, receipts = _inventory()
        _v2_canary_history(TASK_TMP, history.verify_history(TASK_TMP), reservations, receipts)
        if counts["study"]:
            raise evidence.EvidenceError("STUDY_RESERVED_BEFORE_FREEZE")
        if CANARY_PATH.exists():
            admission, _, _ = _verified_admission(TASK_TMP, transport, preflight_result["scientific_sha256"])
            return {"status": "PASS", "admission": admission}
        prior_v2 = []
        for path in sorted(CANARY_RUN_DIR.glob("*.json")):
            previous = _read_json(path)
            if previous.get("provider") == "ollama_local":
                prior_v2.append(previous)
        if not isinstance(changed_premise, str) or not changed_premise.strip():
            raise RuntimeError("explicit changed-premise reason required from historical Codex failure")
        prior_v2.sort(key=lambda item: item["timestamp_utc"])
        if prior_v2 and prior_v2[-1].get("transport") == transport and prior_v2[-1].get("scientific_sha256") == preflight_result["scientific_sha256"]:
            raise RuntimeError("unchanged scientific source and transport cannot be readmitted")
        budget = load_protocol()["turn_budget"]
        if counts["canary"] + 2 > budget["canary"] or sum(counts.values()) + 2 > budget["absolute"]:
            raise RuntimeError("insufficient allowance for both canary predicates")
        marker = "STUDY-CANARY-" + secrets.token_hex(16)
        context = _v2_context(transport, marker, preflight_result["history_sha256"])
        context_hash = evidence.freeze_sha256(context)
        run_id = uuid.uuid4().hex
        summary = {"run_id": run_id, "provider": "ollama_local", "timestamp_utc": utc_now(), "status": "BLOCKED",
                   "scientific_sha256": context["scientific_sha256"], "transport": transport,
                   "changed_premise": changed_premise, "context": context, "attempts": {}}
        try:
            for name, prompt, private_marker in (("structured", STRUCTURED_PROMPT, None), ("marker", MARKER_PROMPT, marker)):
                receipt = _execute_reserved_call(f"canary:{name}", "canary", prompt, sha256_bytes(prompt.encode("utf-8")),
                                                 {"prompt": sha256_bytes(prompt.encode("utf-8"))}, transport, marker=private_marker,
                                                 context_sha256=context_hash, scientific_sha256=context["scientific_sha256"], predicate=name,
                                                 history_sha256=context["history_sha256"])
                summary["attempts"][name] = receipt["attempt_id"]
                expected = context["predicates"][name]
                if (receipt["status"] != "valid" or receipt["verdict"] != expected["verdict"] or
                        (name == "structured" and receipt["reason"] != expected["reason"]) or
                        receipt["tool_event"] is not False or receipt["marker_echo"] is not False):
                    return {"status": "BLOCKED", "failure_status": "CANARY_PREDICATE", "attempts": summary["attempts"]}
                _v2_verify_canary(TASK_TMP, context, name, receipt)
            paths = {name: RECEIPT_DIR / f"{attempt}.json" for name, attempt in summary["attempts"].items()}
            admission = {"schema_version": 2, "provider": "ollama_local", "status": "PASS", "admitted_utc": utc_now(),
                         "scientific_sha256": context["scientific_sha256"], "transport": transport,
                         "history_sha256": context["history_sha256"], "context_sha256": context_hash,
                         "receipt_sha256": {name: _file_digest(path) for name, path in paths.items()}}
            evidence.verify_v2_admission(admission, context, paths,
                                         lambda name, receipt: _v2_verify_canary(TASK_TMP, context, name, receipt))
            _save_json(CANARY_PATH, {"admission": admission, "context": context, "attempts": summary["attempts"]}, create_only=True)
            summary["status"] = "PASS"
            return {"status": "PASS", "admission": admission}
        finally:
            _save_json(CANARY_RUN_DIR / f"{run_id}.json", summary, create_only=True)


def freeze_protocol() -> dict[str, Any]:
    if not _v2_active():
        return _freeze_protocol_v1()
    with _operator_lock():
        preflight_result = _require_passing_preflight()
        if _counts()["study"]:
            raise evidence.EvidenceError("STUDY_RESERVED_BEFORE_FREEZE")
        reservations, receipts = _inventory()
        _v2_canary_history(TASK_TMP, history.verify_history(TASK_TMP), reservations, receipts)
        if FREEZE_PATH.exists():
            raise FileExistsError("freeze already exists")
        transport = _transport_identity(ollama.inspect_runtime())
        if transport != preflight_result["transport"]:
            raise RuntimeError("runtime identity changed")
        admission, context, _ = _verified_admission(TASK_TMP, transport, preflight_result["scientific_sha256"])
        historical = history.verify_history(TASK_TMP)
        if context["history_sha256"] != historical["sha256"]:
            raise evidence.EvidenceError("HISTORY_CHANGED")
        scientific = evidence.scientific_closure(REPO_ROOT)
        protocol, schedule = load_protocol(), ordered_schedule()
        frozen = {"schema_version": 2, "provider": "ollama_local", "frozen_utc": utc_now(),
                  "auth_route": "local_unauthenticated", "scientific_files": scientific,
                  "scientific_sha256": evidence.freeze_sha256(scientific), "protocol": protocol, "schedule": schedule,
                  "transport": transport, "history_sha256": historical["sha256"], "admission": admission}
        digest = evidence.freeze_sha256(frozen)
        evidence.verify_v2_freeze(frozen, digest, scientific_files=scientific, protocol=protocol, schedule=schedule,
                                  transport=transport, history_sha256=historical["sha256"], admission=admission,
                                  verify_admission=lambda value: value == _verified_admission(TASK_TMP, transport, frozen["scientific_sha256"])[0])
        _save_json(FREEZE_PATH, frozen, create_only=True)
        return {"status": "PASS", "freeze_sha256": digest, "study_turns": len(schedule)}


def load_private_bundle(root: Path = TASK_TMP) -> dict[str, Any]:
    """Reopen v2 private evidence without querying a server or installed executable."""
    root = Path(root).resolve()
    frozen = _read_json(root / "freeze.json")
    if frozen.get("schema_version") == 1:
        return _load_private_bundle_v1(root)
    historical = history.verify_history(root)
    scientific = evidence.scientific_closure(REPO_ROOT)
    transport = frozen["transport"]
    if transport["configuration_sha256"] != ollama.configuration_sha256():
        raise evidence.EvidenceError("CONFIGURATION_CHANGED")
    admission, context, _ = _verified_admission(root, transport, evidence.freeze_sha256(scientific))
    freeze_hash = evidence.freeze_sha256(frozen)
    evidence.verify_v2_freeze(frozen, freeze_hash, scientific_files=scientific, protocol=load_protocol(),
                              schedule=ordered_schedule(), transport=transport, history_sha256=historical["sha256"],
                              admission=admission, verify_admission=lambda value: value == admission)
    reservations, receipts, sidecars = (_records(root / name) for name in ("reservations", "receipts", "sidecars"))
    if set(reservations) != set(receipts) or set(reservations) != set(sidecars):
        raise evidence.EvidenceError("INCOMPLETE_INVENTORY")
    _v2_canary_history(root, historical, reservations, receipts)
    counts = {"canary": 0, "study": 0}
    for reservation in reservations.values():
        kind = reservation.get("kind")
        if kind not in counts:
            raise evidence.EvidenceError("RESERVATION_KIND")
        counts[kind] += 1
    budget = load_protocol()["turn_budget"]
    if any(counts[kind] > budget[kind] for kind in counts) or sum(counts.values()) > budget["absolute"]:
        raise evidence.EvidenceError("TURN_BUDGET_EXCEEDED")
    study_reservations = sorted((item for item in reservations.values() if item["kind"] == "study"), key=lambda item: item["schedule_index"])
    study_receipts = [receipts[item["attempt_id"]] for item in study_reservations]
    evidence.verify_v2_inventory(frozen, study_reservations, study_receipts, freeze_hash)
    cases = {case["case_id"]: case for split in ("development", "holdout") for case in load_cases(split)}
    for reservation, receipt in zip(study_reservations, study_receipts):
        attempt = reservation["attempt_id"]
        cell = frozen["schedule"][reservation["schedule_index"]]
        prompt = build_prompt(cases[cell["case_id"]], cell["condition"])
        evidence.verify_v2_private_receipt(frozen, freeze_hash, root / "reservations" / f"{attempt}.json",
                                           root / "receipts" / f"{attempt}.json", root / "sidecars" / f"{attempt}.json",
                                           root, ollama.build_request(prompt), ollama.parse_response)
    return {"verification_scope": "private_raw_verified", "freeze": frozen, "freeze_sha256": freeze_hash,
            "reservations": study_reservations, "receipts": study_receipts, "canary_reservations": counts["canary"],
            "canary_ledger": [item for item in reservations.values() if item["kind"] == "canary"],
            "history": historical, "admission_context": context}


def run_split(split: str, authorize: bool) -> dict[str, Any]:
    if not _v2_active():
        return _run_split_v1(split, authorize)
    if split not in {"development", "holdout"}:
        raise ValueError("split must be development or holdout")
    if not authorize:
        raise RuntimeError("study calls require explicit local-call authorization")
    with _operator_lock():
        preflight_result = _require_passing_preflight()
        bundle = load_private_bundle(TASK_TMP)
        frozen = bundle["freeze"]
        if preflight_result["transport"] != frozen["transport"]:
            raise RuntimeError("transport identity changed")
        receipts = bundle["receipts"]
        if receipts and receipts[-1]["status"] != "valid":
            return {"status": "BLOCKED", "failure_status": receipts[-1]["status"], "new_attempts": 0}
        schedule = frozen["schedule"]
        start = len(receipts)
        if start < len(schedule) and schedule[start]["split"] != split:
            raise RuntimeError("requested split is not the next frozen schedule prefix")
        cases = {case["case_id"]: case for case in load_cases(split)}
        attempted = 0
        for index in range(start, len(schedule)):
            cell = schedule[index]
            if cell["split"] != split:
                break
            prompt = build_prompt(cases[cell["case_id"]], cell["condition"])
            hashes = {key: cell[f"{key}_sha256"] for key in ("code", "task", "criteria", "common_prompt", "prompt")}
            slot = f"study:{split}:{cell['case_id']}:{cell['condition']}"
            receipt = _execute_reserved_call(slot, "study", prompt, hashes["prompt"], hashes, frozen["transport"],
                                             context_sha256=bundle["freeze_sha256"], schedule_index=index,
                                             scientific_sha256=frozen["scientific_sha256"], history_sha256=frozen["history_sha256"])
            attempted += 1
            if receipt["status"] != "valid":
                return {"status": "BLOCKED", "failure_status": receipt["status"], "new_attempts": attempted, "stopped_at": slot}
            bundle = load_private_bundle(TASK_TMP)
        return {"status": "PASS", "split": split, "new_attempts": attempted,
                "valid_existing_calls": start, "total_reserved": _counts()}
