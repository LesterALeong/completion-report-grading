"""Immutable byte custody for the two charged, failed Codex v1 attempts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .evidence import EvidenceError, read_json


ATTEMPT_IDS = ("2a22e64d73ff4fc6826545dd436ae518", "5f300311400440739acbd82b78e33478")
MANIFEST_NAME = "codex-v1-history.json"


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            while chunk := stream.read(65536):
                digest.update(chunk)
    except OSError as error:
        raise EvidenceError("HISTORY_FILE_UNREADABLE") from error
    return digest.hexdigest()


def _inside(root: Path, path: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise EvidenceError("HISTORY_PATH_INVALID")
    return resolved


def _object(path: Path) -> dict[str, Any]:
    value = read_json(path)
    if not isinstance(value, dict):
        raise EvidenceError("HISTORY_OBJECT_INVALID")
    return value


def _snapshot(root: Path) -> dict[str, Any]:
    entries = []
    for attempt in ATTEMPT_IDS:
        paths = {name: _inside(root, root / folder / f"{attempt}.json") for name, folder in (
            ("reservation", "reservations"), ("receipt", "receipts"), ("sidecar", "sidecars"))}
        reservation, receipt, sidecar = (_object(paths[name]) for name in ("reservation", "receipt", "sidecar"))
        if (any(item.get("attempt_id") != attempt for item in (reservation, receipt, sidecar)) or
                reservation.get("kind") != "canary" or reservation.get("slot_id") != "canary:structured" or
                sidecar.get("kind") != "canary" or sidecar.get("slot_id") != reservation["slot_id"] or
                reservation.get("context_sha256") != receipt.get("context_sha256") or
                reservation.get("context_sha256") != sidecar.get("context_sha256") or
                receipt.get("sidecar_sha256") != _digest(paths["sidecar"])):
            raise EvidenceError("HISTORY_IDENTITY_MISMATCH")
        if (receipt.get("status") not in {"protocol_invalid", "operational_unknown"} or
                receipt.get("status") != sidecar.get("status") or receipt.get("verdict") is not None or
                receipt.get("reason") is not None or sidecar.get("verdict") is not None or sidecar.get("reason") is not None):
            raise EvidenceError("HISTORY_DISPOSITION_INVALID")
        for field in ("cleanup_proven", "forced_cleanup", "active_processes_final", "judge_directory_cleaned", "marker_echo", "tool_event"):
            if receipt.get(field) != sidecar.get(field):
                raise EvidenceError("HISTORY_CUSTODY_MISMATCH")
        for name in ("stdout", "stderr", "terminal", "metadata"):
            value = sidecar.get(f"{name}_path")
            if not isinstance(value, str):
                raise EvidenceError("HISTORY_CAPTURE_MISSING")
            paths[name] = _inside(root, Path(value))
            if _digest(paths[name]) != sidecar.get(f"{name}_sha256"):
                raise EvidenceError("HISTORY_CAPTURE_MISMATCH")
            if name in {"stdout", "stderr"} and paths[name].stat().st_size != sidecar.get(f"{name}_bytes"):
                raise EvidenceError("HISTORY_CAPTURE_SIZE")
        terminal, metadata = _object(paths["terminal"]), _object(paths["metadata"])
        if (terminal.get("returncode") != sidecar.get("returncode") or terminal.get("failed_step") is not None or
                terminal.get("fault_code") is not None or not all(type(metadata.get(key)) is int and metadata[key] > 0 for key in ("wrapper_pid", "cli_pid"))):
            raise EvidenceError("HISTORY_TERMINAL_MISMATCH")
        cli = sidecar.get("cli")
        if not isinstance(cli, dict) or not isinstance(cli.get("configuration_sha256"), str) or not isinstance(sidecar.get("scientific_sha256"), str):
            raise EvidenceError("HISTORY_PROVENANCE_MISSING")
        entries.append({"attempt_id": attempt, "provider": "codex_v1", "context_sha256": reservation["context_sha256"],
                        "scientific_sha256": sidecar["scientific_sha256"], "configuration_sha256": cli["configuration_sha256"],
                        "status": receipt["status"], "admitted": False,
                        "artifacts_sha256": {name: _digest(path) for name, path in paths.items()}})
    return {"schema_version": 1, "provider": "codex_v1", "attempts": entries}


def verify_history(root: Path) -> dict[str, Any]:
    """Reopen the create-only manifest and every referenced historical byte."""
    root = Path(root).resolve()
    path = root / MANIFEST_NAME
    manifest = _object(path)
    if manifest != _snapshot(root):
        raise EvidenceError("HISTORY_MANIFEST_MISMATCH")
    return {"manifest": manifest, "sha256": _digest(path)}


def ensure_history(root: Path) -> dict[str, Any]:
    """Create the historical manifest once, or verify the existing one."""
    root = Path(root).resolve()
    path = root / MANIFEST_NAME
    if not path.exists():
        manifest = _snapshot(root)
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(manifest, stream, ensure_ascii=False, sort_keys=True, indent=2)
            stream.write("\n")
    return verify_history(root)
