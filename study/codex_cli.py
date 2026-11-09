"""Closed, shell-free adapter for the installed Codex CLI."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .data import ROOT, load_protocol
from .evidence import EvidenceError, _json
from .protocol import TASK_TMP, canonical_json
from .windows_job import run_native


ALLOWED_EVENTS = {
    "thread.started", "turn.started", "item.started", "item.completed",
    "turn.completed", "turn.failed", "error",
}
ALLOWED_ITEM_TYPES = {"reasoning", "agent_message"}
API_ROUTE_ENVIRONMENT = {
    "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_API_BASE", "OPENAI_ORG_ID",
    "OPENAI_PROJECT_ID", "CODEX_API_KEY", "CODEX_ACCESS_TOKEN", "CODEX_AUTH_TOKEN",
}
DIAGNOSTIC_BYTES = 4096
MAX_PARSE_BYTES = 8 * 1024 * 1024
INSPECTION_TIMEOUT_SECONDS = 15


@dataclass(frozen=True)
class ParsedResponse:
    status: str
    verdict: str | None = None
    reason: str | None = None
    reported_model: str | None = None
    event_count: int = 0
    protocol_violations: tuple[str, ...] = ()
    tool_event: bool = False
    operational_failure: bool = False


@dataclass(frozen=True)
class CaptureSummary:
    """Private stream commitment and independently bounded byte slices."""

    byte_count: int
    sha256: str
    head: bytes
    tail: bytes
    truncated: bool


@dataclass(frozen=True)
class ProcessResult:
    """Transport result; custody and capture fields default to unknown, never proof."""
    status: str
    verdict: str | None
    reason: str | None
    returncode: int | None
    timed_out: bool
    reported_model: str | None
    event_count: int
    cleanup_proven: bool | None = None
    forced_cleanup: bool | None = None
    active_processes_final: int | None = None
    failed_step: str | None = None
    last_completed_step: str | None = None
    fault_code: str | None = None
    stdout_path: Path | None = None
    stderr_path: Path | None = None
    terminal_path: Path | None = None
    metadata_path: Path | None = None
    stdout_capture: CaptureSummary | None = None
    stderr_capture: CaptureSummary | None = None
    protocol_violations: tuple[str, ...] = ()
    tool_event: bool = False
    marker_echo: bool | None = None


def find_executable() -> str:
    executable = shutil.which("codex")
    if executable is None:
        raise FileNotFoundError("installed codex executable was not found")
    return executable


def child_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for name in API_ROUTE_ENVIRONMENT:
        environment.pop(name, None)
    return environment


def configuration_manifest() -> dict[str, Any]:
    protocol = load_protocol()
    return {
        "requested_model": protocol["model"]["requested_alias"],
        "reasoning_effort": protocol["model"]["reasoning_effort"],
        "disabled_features": protocol["cli"]["disabled_features"],
        "config": protocol["cli"]["config"],
        "output_schema_sha256": hashlib.sha256((ROOT / "output.schema.json").read_bytes()).hexdigest(),
        "flags": [
            "--skip-git-repo-check", "--ignore-user-config",
            "--ephemeral", "--json", "--output-schema", "--sandbox", "read-only",
            "--strict-config",
        ],
        "api_route_environment_removed": sorted(API_ROUTE_ENVIRONMENT),
    }


def configuration_sha256() -> str:
    return hashlib.sha256(canonical_json(configuration_manifest())).hexdigest()


def build_argv(executable: str, schema_path: str | Path) -> list[str]:
    protocol = load_protocol()
    argv = [
        executable,
        "exec",
        "--skip-git-repo-check",
        "--ignore-user-config",
        "--ephemeral",
        "--json",
        "--output-schema",
        str(Path(schema_path).resolve()),
        "--sandbox",
        "read-only",
        "--model",
        protocol["model"]["requested_alias"],
        "--strict-config",
    ]
    for feature in protocol["cli"]["disabled_features"]:
        argv.extend(("--disable", feature))
    for key, value in protocol["cli"]["config"].items():
        rendered = json.dumps(value, ensure_ascii=False) if isinstance(value, str) else str(value).lower()
        argv.extend(("--config", f"{key}={rendered}"))
    return argv


def _validate_final(text: str) -> tuple[str, str] | None:
    try:
        value = _json(text.encode("utf-8"))
    except (EvidenceError, TypeError, AttributeError, UnicodeEncodeError):
        return None
    if not isinstance(value, dict) or set(value) != {"verdict", "reason"}:
        return None
    if not isinstance(value["verdict"], str) or value["verdict"] not in {"PASS", "FAIL", "INDETERMINATE"}:
        return None
    if not isinstance(value["reason"], str) or not value["reason"].strip() or len(value["reason"]) > 300:
        return None
    return value["verdict"], value["reason"].strip()


def parse_event_stream(stdout: str, returncode: int | None, timed_out: bool = False) -> ParsedResponse:
    state = "initial"
    final_text = None
    final_seen = False
    event_count = 0
    violations: set[str] = set()
    models: set[str] = set()
    terminal_failure = False
    tool_event = False
    item_states: dict[str, tuple[str, str]] = {}
    allowed_keys = {
        "thread.started": {"type", "thread_id"},
        "turn.started": {"type"},
        "item.started": {"type", "item"},
        "item.completed": {"type", "item"},
        "turn.completed": {"type", "usage", "model", "model_id", "thread_id"},
        "turn.failed": {"type", "error"},
        "error": {"type", "message"},
    }
    for line in stdout.splitlines():
        if not line.strip():
            continue
        event_count += 1
        try:
            event = _json(line.encode("utf-8"))
        except (EvidenceError, UnicodeEncodeError):
            violations.add("malformed_json")
            continue
        if not isinstance(event, dict) or not isinstance(event.get("type"), str) or event["type"] not in ALLOWED_EVENTS:
            violations.add("unknown_event")
            continue
        event_type = event["type"]
        if set(event) - allowed_keys[event_type]:
            violations.add("unknown_envelope_field")
        if event_type in {"turn.failed", "error"}:
            terminal_failure = True
            if state == "terminal":
                violations.add("after_terminal")
            state = "terminal"
            continue
        if (event_type in {"item.started", "item.completed"} and isinstance(event.get("item"), dict)
                and event["item"].get("type") == "error"):
            terminal_failure = True
            continue
        if state == "terminal":
            violations.add("after_terminal")
            continue
        if event_type == "thread.started":
            if state != "initial":
                violations.add("thread_order")
            else:
                state = "thread"
        elif event_type == "turn.started":
            if state != "thread":
                violations.add("turn_order")
            else:
                state = "turn"
        elif event_type in {"item.started", "item.completed"}:
            if state != "turn":
                violations.add("item_outside_turn")
            if final_seen:
                violations.add("item_after_final")
            item = event.get("item")
            if not isinstance(item, dict):
                violations.add("malformed_item")
                continue
            item_type = item.get("type")
            if not isinstance(item_type, str) or item_type not in ALLOWED_ITEM_TYPES:
                tool_event = True
                violations.add("forbidden_item")
                continue
            if set(item) - {"id", "type", "text"}:
                violations.add("unknown_item_field")
            item_id = item.get("id")
            if item_id is not None:
                if not isinstance(item_id, str) or not item_id:
                    violations.add("invalid_item_id")
                elif event_type == "item.started":
                    if item_id in item_states:
                        violations.add("duplicate_item")
                    item_states[item_id] = (item_type, "started")
                else:
                    previous = item_states.get(item_id)
                    if previous is not None and previous != (item_type, "started"):
                        violations.add("item_lifecycle")
                    item_states[item_id] = (item_type, "completed")
            if event_type == "item.completed" and item_type == "agent_message":
                if final_seen:
                    violations.add("duplicate_final")
                final_seen = True
                final_text = item.get("text")
        elif event_type == "turn.completed":
            if state != "turn":
                violations.add("completion_order")
            if any(value[1] == "started" for value in item_states.values()):
                violations.add("unfinished_item")
            for key in ("model", "model_id"):
                if key in event:
                    model = event[key]
                    if not isinstance(model, str) or not re.fullmatch(r"[A-Za-z0-9._-]{1,120}", model):
                        violations.add("invalid_model")
                    else:
                        models.add(model)
            state = "terminal"
    if len(models) > 1:
        violations.add("conflicting_models")
    reported_model = next(iter(models)) if len(models) == 1 else None
    flags = tuple(sorted(violations))
    if terminal_failure or timed_out or returncode != 0:
        return ParsedResponse("operational_unknown", reported_model=reported_model, event_count=event_count, protocol_violations=flags, tool_event=tool_event, operational_failure=terminal_failure)
    if violations:
        return ParsedResponse("protocol_invalid", reported_model=reported_model, event_count=event_count, protocol_violations=flags, tool_event=tool_event)
    if state != "terminal" or not final_seen:
        return ParsedResponse("operational_unknown", reported_model=reported_model, event_count=event_count)
    parsed = _validate_final(final_text)
    if parsed is None:
        return ParsedResponse("invalid_output", reported_model=reported_model, event_count=event_count)
    verdict, reason = parsed
    return ParsedResponse("valid", verdict, reason, reported_model, event_count)


def validate_working_directory(cwd: str | Path, require_empty: bool = True) -> Path:
    working_directory = Path(cwd).resolve()
    try:
        working_directory.relative_to(TASK_TMP)
    except ValueError as error:
        raise ValueError("judge working directory must be under the task temp root") from error
    if not working_directory.is_dir():
        raise ValueError("judge working directory must exist")
    if any((parent / ".git").exists() for parent in (working_directory, *working_directory.parents)):
        raise ValueError("judge working directory must not be inside a Git worktree")
    if require_empty and any(working_directory.iterdir()):
        raise ValueError("study judge working directory must be empty")
    return working_directory


def _capture(path: Path, marker: bytes | None, retain_for_parse: bool) -> tuple[CaptureSummary, bytes | None, bool]:
    digest = hashlib.sha256()
    count = 0
    head = b""
    tail = b""
    parse_bytes = bytearray() if retain_for_parse else None
    marker_seen = False
    overlap = b""
    with path.open("rb") as stream:
        while chunk := stream.read(65536):
            count += len(chunk)
            digest.update(chunk)
            head = (head + chunk)[:DIAGNOSTIC_BYTES]
            tail = (tail + chunk)[-DIAGNOSTIC_BYTES:]
            if marker:
                marker_seen |= marker in overlap + chunk
                overlap = (overlap + chunk)[-(len(marker) - 1):] if len(marker) > 1 else b""
            if parse_bytes is not None:
                if count <= MAX_PARSE_BYTES:
                    parse_bytes.extend(chunk)
                else:
                    parse_bytes = None
    return CaptureSummary(count, digest.hexdigest(), head, tail, count > DIAGNOSTIC_BYTES), bytes(parse_bytes) if parse_bytes is not None else None, marker_seen


def run_codex(prompt: str, cwd: str | Path, timeout_seconds: int, marker: str | None = None) -> ProcessResult:
    working_directory = validate_working_directory(cwd, require_empty=marker is None)
    executable = find_executable()
    argv = build_argv(executable, ROOT / "output.schema.json")
    capture_dir = TASK_TMP / "captures" / uuid.uuid4().hex
    capture_dir.mkdir(parents=True, exist_ok=False)
    try:
        native = run_native(argv, prompt, working_directory, capture_dir, timeout_seconds, env=child_environment())
    except Exception as error:
        return ProcessResult("operational_unknown", None, None, None, False, None, 0,
                             failed_step="native_supervisor", last_completed_step="capture_created",
                             fault_code=type(error).__name__, stdout_path=capture_dir / "stdout.bin",
                             stderr_path=capture_dir / "stderr.bin", terminal_path=capture_dir / "terminal.json",
                             metadata_path=capture_dir / "process.json")

    stdout_capture = stderr_capture = None
    raw_stdout = None
    marker_echo = False
    capture_errors: list[str] = []
    marker_bytes = marker.encode("utf-8") if marker else None
    try:
        stdout_capture, raw_stdout, stdout_marker = _capture(native.stdout_path, marker_bytes, True)
        marker_echo |= stdout_marker
    except OSError as error:
        capture_errors.append(type(error).__name__)
    try:
        stderr_capture, _, stderr_marker = _capture(native.stderr_path, marker_bytes, False)
        marker_echo |= stderr_marker
    except OSError as error:
        capture_errors.append(type(error).__name__)
    flags: set[str] = set()
    if stdout_capture is None:
        parsed = ParsedResponse("operational_unknown")
    elif raw_stdout is None:
        flags.add("stdout_oversized")
        parsed = ParsedResponse("protocol_invalid")
    else:
        try:
            decoded = raw_stdout.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            flags.add("stdout_invalid_utf8")
            parsed = ParsedResponse("protocol_invalid")
        else:
            parsed = parse_event_stream(decoded, native.returncode, native.timed_out)
    flags.update(parsed.protocol_violations)
    if marker_echo:
        flags.add("marker_echo")
    failed = (parsed.operational_failure or native.timed_out or native.returncode != 0 or native.failed_step is not None
              or native.cleanup_proven is not True or native.forced_cleanup is not False
              or native.active_processes_final != 0 or bool(capture_errors))
    status = "operational_unknown" if failed else ("protocol_invalid" if flags else parsed.status)
    failed_step, fault_code = native.failed_step, native.fault_code
    if failed_step is None:
        if native.timed_out:
            failed_step, fault_code = "wait_wrapper", "TIMEOUT"
        elif native.returncode is None:
            failed_step, fault_code = "read_terminal", "MISSING_EXIT"
        elif native.returncode != 0:
            failed_step, fault_code = "child_exit", "NONZERO_EXIT"
        elif native.cleanup_proven is not True or native.forced_cleanup is not False or native.active_processes_final != 0:
            failed_step, fault_code = "cleanup_job", "CUSTODY_UNPROVEN"
        elif capture_errors:
            failed_step, fault_code = "read_capture", capture_errors[0]
        elif status != "valid":
            failed_step, fault_code = "parse_stdout", status.upper()
    return ProcessResult(
        status=status, verdict=parsed.verdict if status == "valid" else None,
        reason=parsed.reason if status == "valid" else None, returncode=native.returncode,
        timed_out=native.timed_out, reported_model=parsed.reported_model, event_count=parsed.event_count,
        cleanup_proven=native.cleanup_proven, forced_cleanup=native.forced_cleanup,
        active_processes_final=native.active_processes_final,
        failed_step=failed_step,
        last_completed_step=native.last_completed_step,
        fault_code=fault_code,
        stdout_path=native.stdout_path, stderr_path=native.stderr_path, terminal_path=native.terminal_path,
        metadata_path=native.metadata_path, stdout_capture=stdout_capture, stderr_capture=stderr_capture,
        protocol_violations=tuple(sorted(flags)), tool_event=parsed.tool_event,
        marker_echo=marker_echo if not capture_errors else None,
    )


def inspect_cli() -> dict[str, Any]:
    executable = find_executable()
    binary_hash = hashlib.sha256(Path(executable).read_bytes()).hexdigest()
    completed = subprocess.run(
        [executable, "--version"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=child_environment(),
        shell=False,
        check=False,
        timeout=INSPECTION_TIMEOUT_SECONDS,
    )
    version_match = re.search(r"^codex-cli\s+(\S+)$", completed.stdout, flags=re.MULTILINE)
    version = version_match.group(1) if completed.returncode == 0 and version_match else None
    return {
        "version": version,
        "binary_sha256": binary_hash,
        "configuration_sha256": configuration_sha256(),
        "version_check_passed": version is not None,
    }


def chatgpt_login_status() -> bool:
    executable = find_executable()
    completed = subprocess.run(
        [executable, "login", "status"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=child_environment(),
        shell=False,
        check=False,
        timeout=INSPECTION_TIMEOUT_SECONDS,
    )
    return completed.returncode == 0 and "Logged in using ChatGPT" in (completed.stdout + completed.stderr)
