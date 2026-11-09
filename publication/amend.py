"""Repair one redaction expansion without changing the frozen study evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

from study import evidence, export, ollama, runner
from study.protocol import canonical_json, sha256_bytes


VERSION = "publication-amendment-v1"
ORIGINAL_MANIFEST = "ef3369c61e24c4b5a6c0417ee5eb8f25b77c4bbde39b86359d12b12c1750f94b"
SCIENTIFIC_ID = "d2c2572ebcf506a162687a318e1410df11c37547f09363ec4d217891ee7f4027"
CANDIDATE_ID = "0424be7750a715f632ef700df04d35cc5e393715ac19c81d5c9aa45b134beafd"
AFFECTED = "e01782c4184246ab94325e2cab896dd7"
ORIGINAL_REASON_HASH = "e6b369c5547ad08ba41707cd26b656e01148124b0ea5a22c898190d00d688ab6"
ORIGINAL_PROJECTION_HASH = "771e5b1606a9970ea7855c70848bfa0779666abbdf05a6942a5d91d3fb8917c0"


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


def amended_projection(raw: bytes, receipt: dict[str, Any], model: str) -> tuple[bytes, str]:
    """Bound only the already-redacted reason and re-run the frozen parser."""
    projection = evidence._json(raw)
    _require(isinstance(projection, dict) and isinstance(projection.get("facts"), dict), "PROJECTION_SCHEMA")
    facts = projection["facts"]
    reason = facts.get("reason")
    _require(receipt.get("status") == "valid" and isinstance(receipt.get("reason"), str) and
             isinstance(reason, str) and reason == evidence._public_reason(receipt["reason"]), "REASON_IDENTITY")
    _require(len(reason) > 300, "NOT_OVERFLOW")
    bounded = reason[:299] + "…"
    _require(bool(bounded.strip()) and len(bounded) <= 300 and evidence._public_reason(bounded) == bounded, "UNSAFE_BOUNDED_REASON")
    facts["reason"] = bounded
    amended = canonical_json(projection)
    result = ollama.parse_projection(amended, model)
    _require((result.status, result.verdict, result.reason, result.reported_model, result.tool_event) ==
             (receipt["status"], receipt["verdict"], bounded, receipt["reported_model"], False), "CLASSIFICATION_CHANGED")
    return amended, bounded


def _read_original(root: Path, manifest_hash: str) -> tuple[dict[str, Any], dict[str, bytes]]:
    manifest_bytes = (root / "manifest.json").read_bytes()
    _require(manifest_hash == ORIGINAL_MANIFEST and sha256_bytes(manifest_bytes) == manifest_hash, "ORIGINAL_MANIFEST")
    manifest = evidence._json(manifest_bytes)
    _require(isinstance(manifest, dict) and set(manifest) == {"schema_version", "provider", "freeze_sha256", "files"} and
             manifest["schema_version"] == 2 and manifest["provider"] == "ollama_local" and isinstance(manifest["files"], dict), "MANIFEST_SCHEMA")
    files = {}
    for name, digest in manifest["files"].items():
        relative = Path(name)
        _require(isinstance(name, str) and not relative.is_absolute() and ".." not in relative.parts and relative.as_posix() == name, "MANIFEST_PATH")
        path = root / relative
        _require(not path.is_symlink() and path.resolve().is_relative_to(root.resolve()) and path.is_file(), "MANIFEST_PATH")
        data = path.read_bytes()
        _require(sha256_bytes(data) == digest, "ORIGINAL_FILE_HASH")
        files[name] = data
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p.name != "manifest.json"}
    _require(actual == set(files), "ORIGINAL_FILE_INVENTORY")
    return manifest, files


def _verify_candidate(repo: Path, private_root: Path, bundle: dict[str, Any]) -> str:
    preflight = evidence.read_json(private_root / "preflight.json")
    files = preflight["candidate_files"]
    _require(len(files) == 56 and preflight["candidate_sha256"] == CANDIDATE_ID and
             sha256_bytes(canonical_json(files)) == CANDIDATE_ID, "CANDIDATE_ID")
    archive_path = private_root / "candidates" / "ollama-v2-candidate-01.zip"
    with zipfile.ZipFile(archive_path) as archive:
        _require(len(archive.namelist()) == 57 and set(archive.namelist()) == set(files) | {"PREFLIGHT.json"}, "CANDIDATE_ARCHIVE_INVENTORY")
        archived_preflight = evidence._json(archive.read("PREFLIGHT.json"))
        _require(archived_preflight["candidate_files"] == files and archived_preflight["candidate_sha256"] == CANDIDATE_ID,
                 "CANDIDATE_ARCHIVE_ID")
        for name, digest in files.items():
            _require(sha256_bytes(archive.read(name)) == digest, "CANDIDATE_ARCHIVE_FILE")
    science = evidence.scientific_closure(repo)
    _require(len(science) == 25 and science == bundle["freeze"]["scientific_files"] and
             evidence.freeze_sha256(science) == SCIENTIFIC_ID, "SCIENTIFIC_CLOSURE")
    return sha256_bytes(archive_path.read_bytes())


def prepare(private_root: Path, original: Path, manifest_hash: str) -> tuple[dict[str, bytes], dict[str, Any]]:
    private_root, original = Path(private_root).resolve(), Path(original).resolve()
    manifest, files = _read_original(original, manifest_hash)
    bundle = runner.load_private_bundle(private_root)
    archive_hash = _verify_candidate(Path(__file__).resolve().parents[1], private_root, bundle)
    frozen = bundle["freeze"]
    _require(manifest["freeze_sha256"] == bundle["freeze_sha256"] and files["freeze.json"] == canonical_json(frozen) and
             files["reservations.json"] == canonical_json(bundle["reservations"]) and len(bundle["receipts"]) == 104, "FREEZE_IDENTITY")
    model = frozen["protocol"]["model"]["requested_alias"]
    public_receipts = evidence._json(files["receipts.json"])
    _require(isinstance(public_receipts, list) and len(public_receipts) == len(bundle["receipts"]) and
             files["receipts.json"] == canonical_json(public_receipts), "RECEIPT_INVENTORY")
    summary = runner._read_json(private_root / "canary-summary.json")
    attempts = [(reservation, receipt, False, index) for index, (reservation, receipt) in enumerate(zip(bundle["reservations"], bundle["receipts"]))]
    for name in ("structured", "marker"):
        attempt = summary["attempts"][name]
        attempts.append((runner._read_json(private_root / "reservations" / f"{attempt}.json"),
                         runner._read_json(private_root / "receipts" / f"{attempt}.json"), True, name))
    changed = []
    for reservation, receipt, canary, position in attempts:
        attempt = receipt["attempt_id"]
        public, projection, http, attestation = export._v2_public_attempt(private_root, receipt, reservation, model, canary=canary)
        _require(files[f"projections/{attempt}.json"] == projection and files[f"transport/{attempt}.json"] == http and
                 files[f"attestations/{attempt}.json"] == attestation, "ORIGINAL_ATTEMPT_BYTES")
        existing_receipt = evidence._json(files[f"admission/{position}.json"]) if canary else public_receipts[position]
        _require(existing_receipt == public and (not canary or files[f"admission/{position}.json"] == canonical_json(public)), "ORIGINAL_RECEIPT")
        projected = evidence._json(projection)
        projected_reason = projected["facts"].get("reason")
        if isinstance(projected_reason, str) and len(projected_reason) > 300:
            _require(not canary and attempt == AFFECTED and sha256_bytes(projection) == ORIGINAL_PROJECTION_HASH and
                     len(receipt["reason"]) == 300 and sha256_bytes(receipt["reason"].encode("utf-8")) == ORIGINAL_REASON_HASH,
                     "UNEXPECTED_OVERFLOW")
            fixed, bounded = amended_projection(projection, receipt, model)
            _require(ollama.parse_projection(projection, model).status == "operational_unknown", "ORIGINAL_NOT_RED")
            files[f"projections/{attempt}.json"] = fixed
            public_receipts[position] = dict(public, reason=bounded)
            attestation_object = evidence._json(attestation)
            attestation_object["projection_sha256"] = sha256_bytes(fixed)
            files[f"attestations/{attempt}.json"] = canonical_json(attestation_object)
            changed.append({"attempt_id": attempt, "original_reason_length": len(receipt["reason"]),
                            "original_reason_sha256": sha256_bytes(receipt["reason"].encode("utf-8")),
                            "redacted_reason_length": len(projected_reason), "redacted_reason_sha256": sha256_bytes(projected_reason.encode("utf-8")),
                            "amended_reason_length": len(bounded), "amended_reason_sha256": sha256_bytes(bounded.encode("utf-8"))})
        else:
            parsed = ollama.parse_projection(projection, model)
            _require((parsed.status, parsed.verdict, parsed.reported_model, parsed.tool_event) ==
                     (receipt["status"], receipt["verdict"], receipt["reported_model"], False), "UNAFFECTED_CLASSIFICATION")
    _require(len(changed) == 1 and changed[0]["attempt_id"] == AFFECTED, "AFFECTED_INVENTORY")
    files["receipts.json"] = canonical_json(public_receipts)
    successor = dict(manifest, files={name: sha256_bytes(data) for name, data in sorted(files.items())})
    successor_bytes = canonical_json(successor)
    files["manifest.json"] = successor_bytes
    provenance = {"schema_version": 1, "version": VERSION, "original_manifest_sha256": manifest_hash,
                  "successor_manifest_sha256": sha256_bytes(successor_bytes), "scientific_sha256": SCIENTIFIC_ID,
                  "prestudy_reviewed_candidate_sha256": CANDIDATE_ID, "candidate_archive_sha256": archive_hash,
                  "publisher_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  "changed_attempts": changed, "change": "Display sanitization only; scientific evidence and grades unchanged."}
    return files, provenance


def publish(private_root: Path, original: Path, target: Path, manifest_hash: str) -> dict[str, Any]:
    target = Path(target).resolve()
    provenance_path = target.with_name(target.name + "-amendment.json")
    _require(not target.exists() and not provenance_path.exists() and not target.is_relative_to(Path(private_root).resolve()) and
             not target.is_relative_to(Path(original).resolve()), "TARGET_NOT_FRESH")
    files, provenance = prepare(private_root, original, manifest_hash)
    target.mkdir(parents=False, exist_ok=False)
    for name, data in sorted(files.items()):
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(data)
    evidence.verify_v2_public_bundle(target, provenance["successor_manifest_sha256"], ollama.parse_projection)
    with provenance_path.open("xb") as stream:
        stream.write(canonical_json(provenance))
    return provenance


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--original-manifest-sha256", required=True)
    args = parser.parse_args()
    print(json.dumps(publish(args.private_root, args.original, args.target, args.original_manifest_sha256), sort_keys=True))


if __name__ == "__main__":
    main()
