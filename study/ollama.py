"""Closed local Ollama adapter and portable response projection."""

from __future__ import annotations

import hashlib
import http.client
import json
import re
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .codex_cli import ProcessResult, ParsedResponse, _capture, _validate_final, validate_working_directory
from .data import ROOT, load_protocol
from .evidence import EvidenceError, _json, _public_reason
from .protocol import TASK_TMP, canonical_json
from .windows_job import run_native


WORKER = Path(__file__).with_name("ollama_worker.py")
ENDPOINT = "http://127.0.0.1:11434"
MAX_BYTES = 8 * 1024 * 1024
HTTP_KEYS = {"schema_version", "endpoint", "route", "request_sha256", "request_bytes", "http_status",
             "body_complete", "body_sha256", "body_bytes", "dispatched", "daemon_completion_uncertain",
             "failed_step", "last_completed_step", "fault_code"}
TRANSPORT_CHECKS = {"native_exit", "no_timeout", "cleanup", "no_forced_cleanup", "no_active_processes",
                    "http_status", "body_complete", "daemon_certain", "dispatched", "http_step",
                    "native_step", "endpoint", "route", "schema", "body_hash", "body_size"}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def configuration_manifest() -> dict[str, Any]:
    protocol = load_protocol()
    return {"provider": protocol["provider"], "model": protocol["model"], "transport": protocol["transport"],
            "schema_sha256": _sha((ROOT / "output.schema.json").read_bytes()),
            "adapter_sha256": _sha(Path(__file__).read_bytes()), "worker_sha256": _sha(WORKER.read_bytes()),
            "decoder_version": 1, "projection_version": 1}


def configuration_sha256() -> str:
    return _sha(canonical_json(configuration_manifest()))


def build_request(prompt: str) -> bytes:
    protocol = load_protocol()
    if protocol["transport"]["endpoint"] != ENDPOINT or not isinstance(prompt, str):
        raise ValueError("invalid endpoint or prompt")
    request = dict(protocol["transport"]["request"])
    request.update({"model": protocol["model"]["requested_alias"],
                    "messages": [{"role": "user", "content": prompt}],
                    "format": _json((ROOT / "output.schema.json").read_bytes())})
    return canonical_json(request)


def _metadata_query(method: str, route: str, body: bytes | None = None) -> dict[str, Any]:
    if (method, route) not in {("GET", "/api/version"), ("GET", "/api/tags"), ("POST", "/api/show")}:
        raise ValueError("unsupported metadata query")
    connection = http.client.HTTPConnection("127.0.0.1", 11434, timeout=15)
    try:
        connection.request(method, route, body=body, headers={"Content-Type": "application/json"})
        response = connection.getresponse()
        raw = response.read(MAX_BYTES + 1)
        if response.status != 200 or len(raw) > MAX_BYTES:
            raise ValueError("metadata response failed")
        value = _json(raw)
        if not isinstance(value, dict):
            raise ValueError("metadata response malformed")
        return value
    finally:
        connection.close()


def inspect_runtime() -> dict[str, Any]:
    protocol = load_protocol()
    expected = protocol["transport"]["expected_runtime"]
    if protocol["transport"]["endpoint"] != ENDPOINT:
        raise ValueError("unsupported endpoint")
    version = _metadata_query("GET", "/api/version")
    tags = _metadata_query("GET", "/api/tags")
    show = _metadata_query("POST", "/api/show", canonical_json({"model": expected["model"]}))
    models = tags.get("models")
    if not isinstance(models, list):
        raise ValueError("malformed tags")
    matches = [item for item in models if isinstance(item, dict) and item.get("name") == expected["model"]]
    if len(matches) != 1:
        raise ValueError("model tag missing or ambiguous")
    tag = matches[0]
    observed = {"server_version": version.get("version"), "model": tag.get("name"),
                "digest": tag.get("digest"), "size": tag.get("size"),
                "capabilities": show.get("capabilities"), "thinking": show.get("thinking"),
                "details": show.get("details"), "parameters": show.get("parameters"),
                "system_sha256": _sha(show.get("system", "").encode("utf-8")),
                "template_sha256": _sha(show["template"].encode("utf-8")),
                "show_fields": list(show)}
    if observed != expected:
        raise ValueError("runtime identity mismatch")
    return {"endpoint": ENDPOINT, "observed": observed,
            "python_version": sys.version, "python_sha256": _sha(Path(sys.executable).read_bytes()),
            "worker_sha256": _sha(WORKER.read_bytes())}


def _safe_model(value: Any) -> str | None:
    return value if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9._:-]{1,120}", value) else None


def _normalise(raw: bytes, facts: dict[str, Any]) -> dict[str, Any]:
    checks = {"native_exit": type(facts.get("terminal_exit")) is int and facts["terminal_exit"] == 0,
              "no_timeout": facts.get("timed_out") is False, "cleanup": facts.get("cleanup_proven") is True,
              "no_forced_cleanup": facts.get("forced_cleanup") is False,
              "no_active_processes": type(facts.get("active_processes_final")) is int and facts["active_processes_final"] == 0,
              "http_status": type(facts.get("http_status")) is int and facts["http_status"] == 200,
              "body_complete": facts.get("body_complete") is True,
              "daemon_certain": facts.get("daemon_completion_uncertain") is False,
              "dispatched": facts.get("dispatched") is True,
              "http_step": "failed_step" in facts and facts["failed_step"] is None,
              "native_step": "native_failed_step" in facts and facts["native_failed_step"] is None,
              "endpoint": facts.get("endpoint") == ENDPOINT, "route": facts.get("route") == "/api/chat",
              "schema": type(facts.get("schema_version")) is int and facts["schema_version"] == 1,
              "body_hash": facts.get("body_sha256") == _sha(raw),
              "body_size": type(facts.get("body_bytes")) is int and facts["body_bytes"] == len(raw)}
    out: dict[str, Any] = {"transport_checks": checks, "envelope_clean": False, "model": None,
                           "tool_violation": False, "thinking_violation": False, "content_valid": False,
                           "verdict": None, "reason": None}
    try:
        if len(raw) > MAX_BYTES:
            return out
        outer = _json(raw)
        json.loads(raw.decode("utf-8"), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    except (EvidenceError, ValueError, RecursionError):
        return out
    if not isinstance(outer, dict):
        return out
    model = _safe_model(outer.get("model"))
    out["model"] = model
    message = outer.get("message")
    if isinstance(message, dict):
        tools = message.get("tool_calls", [])
        out["tool_violation"] = not isinstance(tools, list) or bool(tools)
        thinking = message.get("thinking", "")
        out["thinking_violation"] = not isinstance(thinking, str) or bool(thinking)
    if ("error" in outer or outer.get("done") is not True or model is None
            or not isinstance(message, dict) or message.get("role") != "assistant"
            or not isinstance(message.get("content"), str)):
        return out
    out["envelope_clean"] = True
    parsed = _validate_final(message["content"])
    if parsed is not None:
        out["content_valid"] = True
        out["verdict"], out["reason"] = parsed
    return out


def _classify(facts: dict[str, Any], expected_model: str) -> ParsedResponse:
    model = facts["model"]
    flags = tuple(name for name, key in (("tool_calls", "tool_violation"), ("thinking", "thinking_violation")) if facts[key])
    if not all(facts["transport_checks"].values()) or not facts["envelope_clean"] or model != expected_model:
        return ParsedResponse("operational_unknown", reported_model=model, protocol_violations=flags,
                              tool_event=facts["tool_violation"], operational_failure=True)
    if flags:
        return ParsedResponse("protocol_invalid", reported_model=model, protocol_violations=flags,
                              tool_event=facts["tool_violation"])
    if not facts["content_valid"]:
        return ParsedResponse("invalid_output", reported_model=model)
    return ParsedResponse("valid", facts["verdict"], facts["reason"], model)


def parse_response(body: bytes, transport_facts: dict[str, Any], expected_model: str) -> ParsedResponse:
    return _classify(_normalise(body, transport_facts), expected_model)


def project_response(raw: bytes, transport_facts: dict[str, Any]) -> bytes:
    facts = _normalise(raw, transport_facts)
    if facts["reason"] is not None:
        facts["reason"] = _public_reason(facts["reason"])
    return canonical_json({"schema_version": 1, "provider": "ollama_local", "facts": facts})


def parse_projection(projection: bytes, expected_model: str) -> ParsedResponse:
    try:
        value = _json(projection)
        if not isinstance(value, dict) or set(value) != {"schema_version", "provider", "facts"} or type(value["schema_version"]) is not int or value["schema_version"] != 1 or value["provider"] != "ollama_local":
            raise ValueError("invalid projection")
        facts = value["facts"]
        booleans = {"envelope_clean", "tool_violation", "thinking_violation", "content_valid"}
        if not isinstance(facts, dict) or set(facts) != booleans | {"model", "verdict", "reason", "transport_checks"} or any(type(facts[k]) is not bool for k in booleans):
            raise ValueError("invalid projection facts")
        checks = facts["transport_checks"]
        if not isinstance(checks, dict) or set(checks) != TRANSPORT_CHECKS or any(type(value) is not bool for value in checks.values()):
            raise ValueError("invalid projected transport checks")
        if facts["model"] is not None and _safe_model(facts["model"]) != facts["model"]:
            raise ValueError("invalid model")
        if facts["content_valid"]:
            if _validate_final(canonical_json({"verdict": facts["verdict"], "reason": facts["reason"]}).decode()) != (facts["verdict"], facts["reason"]) or _public_reason(facts["reason"]) != facts["reason"]:
                raise ValueError("invalid projected content")
        elif facts["verdict"] is not None or facts["reason"] is not None:
            raise ValueError("unexpected projected content")
        return _classify(facts, expected_model)
    except (EvidenceError, ValueError, TypeError, KeyError):
        return ParsedResponse("operational_unknown", operational_failure=True)


@dataclass(frozen=True)
class OllamaResult(ProcessResult):
    http_metadata_path: Path | None = None
    request_sha256: str | None = None
    request_bytes: int | None = None
    transport_facts: dict[str, Any] | None = None


def run_ollama(prompt: str, cwd: str | Path, timeout_seconds: int, marker: str | None = None) -> OllamaResult:
    working = validate_working_directory(cwd, require_empty=marker is None)
    request = build_request(prompt)
    capture_dir = TASK_TMP / "captures" / uuid.uuid4().hex
    capture_dir.mkdir(parents=True, exist_ok=False)
    http_path = capture_dir / "http.json"
    request_hash = _sha(request)
    native = None
    try:
        native = run_native([sys.executable, "-I", "-S", "-B", str(WORKER.resolve()), "--http-metadata", str(http_path),
                             "--timeout-seconds", str(timeout_seconds)], request.decode("utf-8"), working, capture_dir,
                            timeout_seconds, cleanup_timeout_seconds=load_protocol()["transport"]["cleanup_timeout_seconds"])
        stdout, raw, marker_stdout = _capture(native.stdout_path, marker.encode("utf-8") if marker else None, True)
        stderr, _, marker_stderr = _capture(native.stderr_path, marker.encode("utf-8") if marker else None, False)
        metadata = _json(http_path.read_bytes())
        if not isinstance(metadata, dict) or set(metadata) != HTTP_KEYS or metadata["request_sha256"] != request_hash or type(metadata["request_bytes"]) is not int or metadata["request_bytes"] != len(request):
            raise ValueError("HTTP metadata mismatch")
        facts = dict(metadata, terminal_exit=native.returncode, timed_out=native.timed_out,
                     cleanup_proven=native.cleanup_proven, forced_cleanup=native.forced_cleanup,
                     active_processes_final=native.active_processes_final, native_failed_step=native.failed_step)
        if raw is None:
            raise ValueError("response exceeds parse limit")
        parsed = parse_response(raw or b"", facts, load_protocol()["model"]["requested_alias"])
        marker_echo = marker_stdout or marker_stderr
        status = "protocol_invalid" if marker_echo and parsed.status != "operational_unknown" else parsed.status
        return OllamaResult(status, parsed.verdict if status == "valid" else None, parsed.reason if status == "valid" else None,
                            native.returncode, native.timed_out, parsed.reported_model, 0,
                            native.cleanup_proven, native.forced_cleanup, native.active_processes_final,
                            native.failed_step or metadata["failed_step"], native.last_completed_step,
                            native.fault_code or metadata["fault_code"], native.stdout_path, native.stderr_path,
                            native.terminal_path, native.metadata_path, stdout, stderr, parsed.protocol_violations,
                            parsed.tool_event, marker_echo, http_path, request_hash, len(request), facts)
    except (OSError, ValueError, EvidenceError, RuntimeError) as error:
        return OllamaResult("operational_unknown", None, None, native.returncode if native else None,
                            native.timed_out if native else False, None, 0,
                            cleanup_proven=native.cleanup_proven if native else None,
                            forced_cleanup=native.forced_cleanup if native else None,
                            active_processes_final=native.active_processes_final if native else None,
                            failed_step="transport_capture", last_completed_step=native.last_completed_step if native else "capture_created",
                            fault_code=type(error).__name__, stdout_path=capture_dir / "stdout.bin",
                            stderr_path=capture_dir / "stderr.bin", terminal_path=capture_dir / "terminal.json",
                            metadata_path=capture_dir / "process.json", http_metadata_path=http_path,
                            request_sha256=request_hash, request_bytes=len(request))
