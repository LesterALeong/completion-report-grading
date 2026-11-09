"""Create a deterministic, portable projection from a verified private bundle."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from . import codex_cli, evidence, ollama, runner
from .protocol import canonical_json, sha256_bytes


def _safe_cli(cli: Any) -> dict[str, Any]:
    keys = {"version", "binary_sha256", "configuration_sha256", "version_check_passed"}
    if (not isinstance(cli, dict) or set(cli) != keys or cli["version_check_passed"] is not True or
            not isinstance(cli["version"], str) or re.fullmatch(r"[A-Za-z0-9._+-]{1,120}", cli["version"]) is None or
            not all(isinstance(cli[key], str) and re.fullmatch(r"[0-9a-f]{64}", cli[key]) for key in ("binary_sha256", "configuration_sha256"))):
        raise evidence.EvidenceError("UNSAFE_CLI_IDENTITY")
    return dict(cli)


def _read_bounded(path: Path, limit: int = codex_cli.MAX_PARSE_BYTES) -> bytes:
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise evidence.EvidenceError("PUBLIC_STDOUT_OVERSIZED")
    return data


def _v2_public_attempt(
    private_root: Path,
    receipt: dict[str, Any],
    reservation: dict[str, Any],
    expected_model: str,
    *,
    canary: bool,
) -> tuple[dict[str, Any], bytes, bytes, bytes]:
    reservation_path = private_root / "reservations" / f"{receipt['attempt_id']}.json"
    reservation_bytes = reservation_path.read_bytes()
    sidecar_path = private_root / "sidecars" / f"{receipt['attempt_id']}.json"
    sidecar_bytes = sidecar_path.read_bytes()
    if (sha256_bytes(reservation_bytes) != receipt["reservation_sha256"] or
            sha256_bytes(sidecar_bytes) != receipt["sidecar_sha256"]):
        raise evidence.EvidenceError("PUBLIC_PRIVATE_IDENTITY")
    sidecar = evidence.read_json(sidecar_path)
    if (sidecar.get("attempt_id") != receipt["attempt_id"] or sidecar.get("slot_id") != reservation["slot_id"] or
            sidecar.get("context_sha256") != receipt.get("freeze_sha256", receipt.get("context_sha256"))):
        raise evidence.EvidenceError("PUBLIC_PRIVATE_IDENTITY")
    raw = _read_bounded(runner._private_path(sidecar["stdout_path"], private_root), ollama.MAX_BYTES)
    http_path = runner._private_path(sidecar["http_metadata_path"], private_root)
    http_bytes = _read_bounded(http_path, ollama.MAX_BYTES)
    if (sha256_bytes(raw) != sidecar["stdout_sha256"] or len(raw) != sidecar["stdout_bytes"] or
            sha256_bytes(http_bytes) != sidecar["transport_metadata_sha256"]):
        raise evidence.EvidenceError("PUBLIC_RAW_CUSTODY")
    http = evidence._json(http_bytes)
    facts = dict(http, terminal_exit=sidecar["terminal_exit"], timed_out=sidecar["timed_out"],
                 cleanup_proven=sidecar["cleanup_proven"], forced_cleanup=sidecar["forced_cleanup"],
                 active_processes_final=sidecar["active_processes_final"], native_failed_step=sidecar["native_failed_step"])
    projection = ollama.project_response(raw, facts)
    parsed = ollama.parse_projection(projection, expected_model)
    public_receipt = dict(receipt)
    public_receipt["reason"] = parsed.reason
    if canary:
        receipt_path = private_root / "receipts" / f"{receipt['attempt_id']}.json"
        public_receipt["private_receipt_sha256"] = sha256_bytes(receipt_path.read_bytes())
    attestation = canonical_json({"raw_sha256": sha256_bytes(raw), "raw_bytes": len(raw),
                                  "projection_sha256": sha256_bytes(projection),
                                  "transport_metadata_sha256": sha256_bytes(http_bytes)})
    return public_receipt, projection, http_bytes, attestation


def _export_v2_public_bundle(private_root: Path, target: Path, bundle: dict[str, Any]) -> dict[str, Any]:
    frozen = bundle["freeze"]
    if frozen.get("provider") != "ollama_local":
        raise evidence.EvidenceError("UNSUPPORTED_PUBLIC_PROVIDER")
    history = bundle["history"]
    if not isinstance(history, dict) or not isinstance(history.get("manifest"), dict):
        raise evidence.EvidenceError("HISTORY_BUNDLE_SCHEMA")
    history_path = private_root / runner.history.MANIFEST_NAME
    history_bytes = history_path.read_bytes()
    if sha256_bytes(history_bytes) != history["sha256"] or history["sha256"] != frozen["history_sha256"]:
        raise evidence.EvidenceError("HISTORY_BUNDLE_DIGEST")

    files: dict[str, bytes] = {
        "freeze.json": canonical_json(frozen),
        "reservations.json": canonical_json(bundle["reservations"]),
        "receipts.json": canonical_json(bundle["receipts"]),
        "history.json": history_bytes,
        "admission/context.json": canonical_json(bundle["admission_context"]),
    }
    canary_summary = runner._read_json(private_root / "canary-summary.json")
    admitted_attempts = canary_summary["attempts"]
    for name in ("structured", "marker"):
        attempt = admitted_attempts[name]
        receipt = runner._read_json(private_root / "receipts" / f"{attempt}.json")
        reservation = runner._read_json(private_root / "reservations" / f"{attempt}.json")
        public_receipt, projection, http, attestation = _v2_public_attempt(
            private_root, receipt, reservation, frozen["protocol"]["model"]["requested_alias"], canary=True
        )
        files[f"admission/{name}.json"] = canonical_json(public_receipt)
        files[f"projections/{attempt}.json"] = projection
        files[f"transport/{attempt}.json"] = http
        files[f"attestations/{attempt}.json"] = attestation

    ledger = []
    historical = {item["attempt_id"]: item for item in history["manifest"]["attempts"]}
    reservations_by_id = {item["attempt_id"]: item for item in bundle["canary_ledger"]}
    for attempt, row in historical.items():
        reservation_path = private_root / "reservations" / f"{attempt}.json"
        reservation = runner._read_json(reservation_path)
        ledger.append({"attempt_id": attempt, "provider": "codex_v1", "kind": "canary",
                       "slot_id": reservation["slot_id"], "reserved_utc": reservation["reserved_utc"],
                       "context_sha256": row["context_sha256"], "status": row["status"], "verdict": None,
                       "reservation_sha256": row["artifacts_sha256"]["reservation"],
                       "receipt_sha256": row["artifacts_sha256"]["receipt"],
                       "sidecar_sha256": row["artifacts_sha256"]["sidecar"], "admitted": False})
    for attempt, reservation in reservations_by_id.items():
        if attempt in historical:
            continue
        receipt_path = private_root / "receipts" / f"{attempt}.json"
        receipt = runner._read_json(receipt_path)
        ledger.append({"attempt_id": attempt, "provider": "ollama_local", "kind": "canary",
                       "slot_id": reservation["slot_id"], "reserved_utc": reservation["reserved_utc"],
                       "context_sha256": reservation["context_sha256"], "status": receipt["status"],
                       "verdict": receipt["verdict"],
                       "reservation_sha256": sha256_bytes((private_root / "reservations" / f"{attempt}.json").read_bytes()),
                       "receipt_sha256": sha256_bytes(receipt_path.read_bytes()),
                       "sidecar_sha256": receipt["sidecar_sha256"], "admitted": attempt in admitted_attempts.values()})
    files["canary_ledger.json"] = canonical_json(sorted(ledger, key=lambda row: (row["reserved_utc"], row["attempt_id"])))

    public_receipts = []
    for reservation, receipt in zip(bundle["reservations"], bundle["receipts"]):
        public_receipt, projection, http, attestation = _v2_public_attempt(
            private_root, receipt, reservation, frozen["protocol"]["model"]["requested_alias"], canary=False
        )
        public_receipts.append(public_receipt)
        attempt = receipt["attempt_id"]
        files[f"projections/{attempt}.json"] = projection
        files[f"transport/{attempt}.json"] = http
        files[f"attestations/{attempt}.json"] = attestation
    files["receipts.json"] = canonical_json(public_receipts)

    manifest = {"schema_version": 2, "provider": "ollama_local", "freeze_sha256": bundle["freeze_sha256"],
                "files": {name: sha256_bytes(data) for name, data in sorted(files.items())}}
    manifest_bytes = canonical_json(manifest)
    manifest_hash = sha256_bytes(manifest_bytes)
    target.mkdir(parents=False, exist_ok=False)
    for name, data in sorted(files.items()):
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(data)
    with (target / "manifest.json").open("xb") as stream:
        stream.write(manifest_bytes)
    verified = evidence.verify_v2_public_bundle(target, manifest_hash, ollama.parse_projection)
    return {"status": "PASS", "manifest_sha256": manifest_hash, "freeze_sha256": bundle["freeze_sha256"],
            "verification_scope": verified["verification_scope"], "study_attempts": len(bundle["receipts"]),
            "canary_attempts": len(ledger)}


def export_public_bundle(private_root: Path, target: Path) -> dict[str, Any]:
    """Create only a new bundle; private verification and privacy review remain distinct."""
    private_root = Path(private_root).resolve()
    target = Path(target).resolve()
    if target.is_relative_to(private_root):
        raise evidence.EvidenceError("PUBLIC_TARGET_INSIDE_PRIVATE_ROOT")
    if target.exists():
        raise FileExistsError("public bundle target already exists")
    bundle = runner.load_private_bundle(private_root)
    frozen = bundle["freeze"]
    if frozen.get("schema_version") == 2:
        return _export_v2_public_bundle(private_root, target, bundle)
    if frozen.get("schema_version") != 1:
        raise evidence.EvidenceError("UNSUPPORTED_FREEZE_SCHEMA")
    _safe_cli(frozen["cli"])
    summary = runner._read_json(private_root / "canary-summary.json")
    context, admission, attempts = summary["context"], summary["admission"], summary["attempts"]
    files: dict[str, bytes] = {
        "freeze.json": canonical_json(frozen), "reservations.json": canonical_json(bundle["reservations"]),
        "admission/context.json": canonical_json(context),
    }
    public_receipts = []
    for reservation, receipt in zip(bundle["reservations"], bundle["receipts"]):
        sidecar = runner._verify_sidecar(private_root, receipt, reservation)
        stdout = _read_bounded(runner._private_path(sidecar["stdout_path"], private_root))
        projection = evidence.project_stdout(stdout)
        attestation = evidence.verify_projection(stdout, projection, receipt, codex_cli.parse_event_stream)
        public_receipt = dict(receipt)
        if public_receipt["reason"] is not None:
            public_receipt["reason"] = evidence._public_reason(public_receipt["reason"])
        public_receipts.append(public_receipt)
        attempt = receipt["attempt_id"]
        files[f"projections/{attempt}.jsonl"] = projection
        files[f"attestations/{attempt}.json"] = canonical_json(attestation)
    files["receipts.json"] = canonical_json(public_receipts)
    admitted = set(attempts.values())
    for name in ("structured", "marker"):
        attempt = attempts[name]
        receipt_path = private_root / "receipts" / f"{attempt}.json"
        receipt_bytes = receipt_path.read_bytes()
        if sha256_bytes(receipt_bytes) != admission["receipt_sha256"][name]:
            raise evidence.EvidenceError("ADMISSION_RECEIPT_DIGEST")
        receipt = evidence.read_json(receipt_path)
        if evidence._public_reason(receipt["reason"]) != receipt["reason"]:
            raise evidence.EvidenceError("UNSAFE_ADMISSION_REASON")
        reservation = runner._read_json(private_root / "reservations" / f"{attempt}.json")
        sidecar = runner._verify_sidecar(private_root, receipt, reservation, context)
        raw = _read_bounded(runner._private_path(sidecar["stdout_path"], private_root))
        if sha256_bytes(raw) != sidecar["stdout_sha256"] or len(raw) != sidecar["stdout_bytes"]:
            raise evidence.EvidenceError("CANARY_RAW_CHANGED")
        projection = evidence.project_stdout(raw)
        replayed = codex_cli.parse_event_stream(projection.decode("utf-8"), 0, False)
        if (replayed.status, replayed.verdict, replayed.reason, replayed.tool_event) != ("valid", receipt["verdict"], receipt["reason"], False):
            raise evidence.EvidenceError("CANARY_PROJECTION_MISMATCH")
        attestation = {"raw_sha256": sha256_bytes(raw), "raw_bytes": len(raw), "projection_sha256": sha256_bytes(projection),
                       "sidecar_sha256": receipt["sidecar_sha256"]}
        files[f"admission/{name}.json"] = receipt_bytes
        files[f"projections/{attempt}.jsonl"] = projection
        files[f"attestations/{attempt}.json"] = canonical_json(attestation)
    ledger = []
    for reservation in sorted(bundle["canary_ledger"], key=lambda item: (item["reserved_utc"], item["attempt_id"])):
        attempt = reservation["attempt_id"]
        receipt_path = private_root / "receipts" / f"{attempt}.json"
        receipt = runner._read_json(receipt_path)
        sidecar = runner._read_json(private_root / "sidecars" / f"{attempt}.json")
        ledger.append({"attempt_id": attempt, "slot_id": reservation["slot_id"], "reserved_utc": reservation["reserved_utc"],
                       "context_sha256": reservation["context_sha256"], "status": receipt["status"], "verdict": receipt["verdict"],
                       "receipt_sha256": sha256_bytes(receipt_path.read_bytes()), "sidecar_sha256": receipt["sidecar_sha256"],
                       "scientific_sha256": sidecar["scientific_sha256"], "cli": _safe_cli(sidecar["cli"]), "admitted": attempt in admitted})
    files["canary_ledger.json"] = canonical_json(ledger)
    manifest = {"schema_version": 1, "freeze_sha256": bundle["freeze_sha256"],
                "files": {name: sha256_bytes(data) for name, data in sorted(files.items())}}
    manifest_bytes = canonical_json(manifest)
    manifest_hash = sha256_bytes(manifest_bytes)
    target.mkdir(parents=False, exist_ok=False)
    for name, data in sorted(files.items()):
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(data)
    with (target / "manifest.json").open("xb") as stream:
        stream.write(manifest_bytes)
    verified = evidence.verify_public_bundle(target, manifest_hash, codex_cli.parse_event_stream)
    return {"status": "PASS", "manifest_sha256": manifest_hash, "freeze_sha256": bundle["freeze_sha256"],
            "verification_scope": verified["verification_scope"], "study_attempts": len(public_receipts), "canary_attempts": len(ledger)}
