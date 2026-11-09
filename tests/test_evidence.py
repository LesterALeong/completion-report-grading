import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from study.codex_cli import parse_event_stream
from study.evidence import (
    EvidenceError, freeze_sha256, project_stdout, read_json, scientific_closure,
    verify_freeze, verify_inventory, verify_private_receipt, verify_projection, verify_public_bundle,
)
from study.protocol import TASK_TMP, canonical_json


def digest(data):
    return hashlib.sha256(data).hexdigest()


def stream(reason="checked", verdict="PASS"):
    events = [
        {"type": "thread.started", "thread_id": "private-thread-id"},
        {"type": "turn.started"},
        {"type": "item.completed", "item": {"id": "private-item-id", "type": "agent_message",
                                                   "text": json.dumps({"verdict": verdict, "reason": reason})}},
        {"type": "turn.completed", "model": "backend-1"},
    ]
    return ("\n".join(map(json.dumps, events)) + "\n").encode()


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        TASK_TMP.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="evidence-", dir=TASK_TMP)
        self.root = Path(self.temp.name)
        (self.root / "study").mkdir()
        (self.root / "docs").mkdir()
        (self.root / "study" / "code.py").write_text("value = 1\n", encoding="utf-8")
        (self.root / "docs" / "SPEC.md").write_text("spec\n", encoding="utf-8")
        self.files = scientific_closure(self.root)
        self.cli = {"version": "example", "binary_sha256": "a" * 64, "configuration_sha256": "b" * 64, "version_check_passed": True}
        self.protocol = {"model": {"requested_alias": "alias", "reasoning_effort": "medium"}, "turn_budget": {"study": 1, "canary": 16, "absolute": 17}}
        self.cell = {"split": "development", "case_id": "D01", "condition": "neutral"}
        self.cell.update({f"{key}_sha256": digest(key.encode()) for key in ("code", "task", "criteria", "common_prompt", "prompt")})
        science = freeze_sha256(self.files)
        self.context = {"scientific_sha256": science, "cli": self.cli, "requested_model": "alias", "reasoning_effort": "medium",
                        "predicates": {"structured": {"prompt_sha256": "1" * 64, "verdict": "PASS", "reason": "structured response available"},
                                       "marker": {"prompt_sha256": "2" * 64, "marker_sha256": "3" * 64, "verdict": "INDETERMINATE"}}}
        context_hash = freeze_sha256(self.context)
        self.canary_paths = {}
        receipt_hashes = {}
        for name in ("structured", "marker"):
            canary = {"attempt_id": name, "predicate": name, "context_sha256": context_hash, "sidecar_sha256": "4" * 64, "status": "valid",
                      "verdict": self.context["predicates"][name]["verdict"],
                      "reason": "structured response available" if name == "structured" else "no access",
                      "tool_event": False, "marker_echo": False, "cleanup_proven": True, "forced_cleanup": False,
                      "active_processes_final": 0, "judge_directory_cleaned": True}
            data = canonical_json(canary)
            path = self.root / f"{name}.json"
            path.write_bytes(data)
            self.canary_paths[name] = path
            receipt_hashes[name] = digest(data)
        self.admission = {"schema_version": 1, "status": "PASS", "admitted_utc": "2026-11-09T12:00:00Z", "scientific_sha256": science, "cli": self.cli,
                          "context_sha256": context_hash, "receipt_sha256": receipt_hashes}
        self.freeze = {"schema_version": 1, "frozen_utc": "2026-11-09T12:01:00Z", "scientific_files": self.files, "scientific_sha256": science,
                       "protocol": self.protocol, "schedule": [self.cell], "cli": self.cli,
                       "auth_route": "chatgpt_subscription", "admission": self.admission}
        self.freeze_hash = freeze_sha256(self.freeze)
        self.reservation = {"schema_version": 1, "attempt_id": "attempt1", "slot_id": "study:development:D01:neutral",
                            "kind": "study", "schedule_index": 0, "reserved_utc": "2026-11-09T12:00:00Z", "freeze_sha256": self.freeze_hash}
        self.raw = stream()
        self.stderr = b"private diagnostic"
        self.receipt = {
            **self.reservation, "scientific_sha256": science, "cli": self.cli,
            "requested_model": "alias", "reasoning_effort": "medium",
            "input_sha256": {key: self.cell[f"{key}_sha256"] for key in ("code", "task", "criteria", "common_prompt", "prompt")},
            "status": "valid", "verdict": "PASS", "reason": "checked", "reported_model": "backend-1",
            "terminal_exit": 0, "timed_out": False, "cleanup_proven": True, "forced_cleanup": False,
            "active_processes_final": 0, "judge_directory_cleaned": True,
            "stdout_sha256": digest(self.raw), "stderr_sha256": digest(self.stderr),
            "stdout_bytes": len(self.raw), "stderr_bytes": len(self.stderr), "timestamp_utc": "2026-11-09T12:00:00Z", "sidecar_sha256": "4" * 64,
        }
        self.stdout_path = self.root / "stdout.bin"
        self.stderr_path = self.root / "stderr.bin"
        self.stdout_path.write_bytes(self.raw)
        self.stderr_path.write_bytes(self.stderr)

    def tearDown(self):
        self.temp.cleanup()

    def test_scientific_closure_ignores_readme_and_detects_code(self):
        (self.root / "README.md").write_text("changed", encoding="utf-8")
        self.assertEqual(scientific_closure(self.root), self.files)
        (self.root / "study" / "code.py").write_text("value = 2\n", encoding="utf-8")
        self.assertNotEqual(scientific_closure(self.root), self.files)

    def test_freeze_exact_joins(self):
        self.assertEqual(verify_freeze(self.freeze, self.freeze_hash, scientific_files=self.files,
                                      protocol=self.protocol, schedule=[self.cell], cli=self.cli, admission=self.admission,
                                      admission_context=self.context, admission_receipt_paths=self.canary_paths,
                                      verify_admission_receipt=lambda name, receipt: True), self.freeze_hash)
        for key, bad in (("protocol", {}), ("schedule", []), ("cli", {}), ("admission", {}), ("scientific_files", {})):
            arguments = dict(scientific_files=self.files, protocol=self.protocol, schedule=[self.cell], cli=self.cli, admission=self.admission,
                             admission_context=self.context, admission_receipt_paths=self.canary_paths,
                             verify_admission_receipt=lambda name, receipt: True)
            arguments[key] = bad
            with self.subTest(key=key), self.assertRaises(EvidenceError):
                verify_freeze(self.freeze, self.freeze_hash, **arguments)

    def test_admission_requires_original_receipts_and_private_verification(self):
        arguments = dict(scientific_files=self.files, protocol=self.protocol, schedule=[self.cell], cli=self.cli, admission=self.admission,
                         admission_context=self.context, admission_receipt_paths=self.canary_paths,
                         verify_admission_receipt=lambda name, receipt: False)
        with self.assertRaises(EvidenceError):
            verify_freeze(self.freeze, self.freeze_hash, **arguments)
        arguments["verify_admission_receipt"] = lambda name, receipt: True
        self.canary_paths["marker"].write_text("{}", encoding="utf-8")
        with self.assertRaises(EvidenceError):
            verify_freeze(self.freeze, self.freeze_hash, **arguments)

    def test_private_replay_and_mutations(self):
        def verify(receipt):
            return verify_private_receipt(self.freeze, self.freeze_hash, self.reservation, receipt,
                                          self.stdout_path, self.stderr_path, parse_event_stream)
        self.assertEqual(verify(self.receipt)["verification_scope"], "private_raw_verified")
        mutations = {"cleanup_proven": False, "forced_cleanup": True, "active_processes_final": False,
                     "judge_directory_cleaned": None, "requested_model": "other", "cli": {},
                     "stdout_sha256": "0" * 64, "verdict": "FAIL", "input_sha256": {}}
        for key, value in mutations.items():
            receipt = copy.deepcopy(self.receipt)
            receipt[key] = value
            with self.subTest(key=key), self.assertRaises(EvidenceError):
                verify(receipt)
        self.stderr_path.write_bytes(b"tampered")
        with self.assertRaises(EvidenceError):
            verify(self.receipt)

    def test_failed_custody_remains_unknown_even_with_valid_raw_final(self):
        receipt = copy.deepcopy(self.receipt)
        receipt.update(status="operational_unknown", verdict=None, reason=None,
                       cleanup_proven=False, forced_cleanup=True)
        verified = verify_private_receipt(self.freeze, self.freeze_hash, self.reservation, receipt,
                                          self.stdout_path, self.stderr_path, parse_event_stream)
        self.assertEqual(verified["receipt"]["status"], "operational_unknown")

    def test_invalid_utf8_private_capture_blocks_explicitly(self):
        self.stdout_path.write_bytes(b"\xff")
        receipt = copy.deepcopy(self.receipt)
        receipt.update(status="protocol_invalid", verdict=None, reason=None,
                       stdout_sha256=digest(b"\xff"), stdout_bytes=1)
        with self.assertRaisesRegex(EvidenceError, "RAW_REPLAY_FAILED"):
            verify_private_receipt(self.freeze, self.freeze_hash, self.reservation, receipt,
                                   self.stdout_path, self.stderr_path, parse_event_stream)

    def test_inventory_refuses_duplicates_missing_and_backend_changes(self):
        verify_inventory(self.freeze, [self.reservation], [self.receipt], self.freeze_hash)
        with self.assertRaises(EvidenceError):
            verify_inventory(self.freeze, [self.reservation], [], self.freeze_hash)
        with self.assertRaises(EvidenceError):
            verify_inventory(self.freeze, [self.reservation, self.reservation], [self.receipt, self.receipt], self.freeze_hash)
        invalid = {**self.reservation, "schema_version": True}
        invalid_receipt = {**self.receipt, "schema_version": True}
        with self.assertRaises(EvidenceError):
            verify_inventory(self.freeze, [invalid], [invalid_receipt], self.freeze_hash)

    def test_projection_is_private_bound_and_public_replay_is_portable(self):
        projection = project_stdout(self.raw)
        self.assertNotIn(b"private-thread-id", projection)
        self.assertNotIn(b"private-item-id", projection)
        verification = verify_projection(self.raw, projection, self.receipt, parse_event_stream)
        self.assertEqual(verification["projection_sha256"], digest(projection))
        public = self.root / "public"
        (public / "projections").mkdir(parents=True)
        (public / "admission").mkdir()
        (public / "attestations").mkdir()
        files = {"freeze.json": canonical_json(self.freeze), "reservations.json": canonical_json([self.reservation]),
                 "receipts.json": canonical_json([self.receipt]), "projections/attempt1.jsonl": projection,
                 "admission/context.json": canonical_json(self.context),
                 "admission/structured.json": self.canary_paths["structured"].read_bytes(),
                 "admission/marker.json": self.canary_paths["marker"].read_bytes(),
                 "projections/structured.jsonl": project_stdout(stream("structured response available")),
                 "projections/marker.jsonl": project_stdout(stream("no access", "INDETERMINATE")),
                 "attestations/attempt1.json": canonical_json(verification)}
        ledger = []
        for name in ("structured", "marker"):
            receipt_bytes = self.canary_paths[name].read_bytes()
            canary = json.loads(receipt_bytes)
            projection = files[f"projections/{name}.jsonl"]
            raw = stream(canary["reason"], canary["verdict"])
            files[f"attestations/{name}.json"] = canonical_json({"raw_sha256": digest(raw), "raw_bytes": len(raw),
                                                                  "projection_sha256": digest(projection), "sidecar_sha256": canary["sidecar_sha256"]})
            ledger.append({"attempt_id": name, "slot_id": f"canary:{name}", "reserved_utc": "2026-11-09T12:00:00Z",
                           "context_sha256": self.admission["context_sha256"], "status": canary["status"], "verdict": canary["verdict"],
                           "receipt_sha256": digest(receipt_bytes), "sidecar_sha256": canary["sidecar_sha256"],
                           "scientific_sha256": self.freeze["scientific_sha256"], "cli": self.cli, "admitted": True})
        files["canary_ledger.json"] = canonical_json(ledger)
        for name, data in files.items():
            (public / name).write_bytes(data)
        manifest = {"schema_version": 1, "freeze_sha256": self.freeze_hash, "files": {name: digest(data) for name, data in files.items()}}
        manifest_bytes = canonical_json(manifest)
        (public / "manifest.json").write_bytes(manifest_bytes)
        self.stdout_path.unlink()
        self.stderr_path.unlink()
        result = verify_public_bundle(public, digest(manifest_bytes), parse_event_stream)
        self.assertEqual(result["verification_scope"], "public_projection_replay")
        self.assertEqual(result["freeze"], self.freeze)
        self.assertEqual(result["reservations"], [self.reservation])
        self.assertEqual(result["admission_context"], self.context)
        self.assertIn("not independently", result["raw_byte_verification"])
        (public / "projections" / "attempt1.jsonl").write_bytes(b"tampered")
        with self.assertRaises(EvidenceError):
            verify_public_bundle(public, digest(manifest_bytes), parse_event_stream)
        with self.assertRaises(EvidenceError):
            verify_private_receipt(self.freeze, self.freeze_hash, self.reservation, self.receipt,
                                   self.stdout_path, self.stderr_path, parse_event_stream)

    def test_projection_retains_failure_classification_and_no_private_text(self):
        valid = [json.loads(line) for line in stream().splitlines()]
        variants = [
            b"{broken\n",
            b"\n".join((json.dumps(valid[0]).encode(), json.dumps(valid[1]).encode(),
                         b'{"type":"item.started","item":{"type":"command_execution","command":"private"}}')),
            b"\n".join((json.dumps(valid[0]).encode(), json.dumps(valid[1]).encode(),
                         b'{"type":"item.completed","item":{"type":"agent_message","text":"PRIVATE INVALID"}}',
                         json.dumps(valid[3]).encode())),
            b"\n".join((json.dumps(valid[0]).encode(), json.dumps(valid[1]).encode(),
                         b'{"type":"new.private-event","secret":"hidden"}')),
        ]
        for raw in variants:
            with self.subTest(raw=raw[:20]):
                projection = project_stdout(raw)
                original = parse_event_stream(raw.decode(), 0)
                public = parse_event_stream(projection.decode(), 0)
                self.assertEqual((public.status, public.verdict, public.reported_model),
                                 (original.status, original.verdict, original.reported_model))
                self.assertNotIn(b"private", projection.lower())
                self.assertNotIn(b"hidden", projection.lower())

    def test_projection_sanitizes_relative_paths(self):
        projection = project_stdout(stream("checked private/file.txt and folder\\secret.txt"))
        self.assertNotIn(b"private/file.txt", projection)
        self.assertNotIn(b"folder", projection)
        self.assertIn(b"[path omitted]", projection)

    def test_corrupt_json_is_not_silently_skipped(self):
        path = self.root / "corrupt.json"
        path.write_text('{"a":1,"a":2}', encoding="utf-8")
        with self.assertRaises(EvidenceError):
            read_json(path)
        with self.assertRaises(EvidenceError):
            read_json(self.root / "missing.json")


if __name__ == "__main__":
    unittest.main()
