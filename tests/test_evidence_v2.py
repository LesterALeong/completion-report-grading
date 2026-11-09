import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from study import evidence, ollama, runner
from study.data import load_cases, load_protocol
from study.prompt import build_prompt
from study.protocol import TASK_TMP, canonical_json


def sha(value):
    return hashlib.sha256(value).hexdigest()


class EvidenceV2Tests(unittest.TestCase):
    def setUp(self):
        TASK_TMP.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="evidence-v2-", dir=TASK_TMP)
        self.root = Path(self.temp.name)
        self.protocol = copy.deepcopy(load_protocol())
        self.protocol["turn_budget"]["study"] = 1
        self.cell = runner.ordered_schedule()[0]
        self.files = {"study/a.py": "a" * 64, "docs/SPEC.md": "b" * 64}
        self.runtime = {"endpoint": "http://127.0.0.1:11434", "observed": self.protocol["transport"]["expected_runtime"],
                        "python_version": "synthetic", "python_sha256": "c" * 64, "worker_sha256": "d" * 64}
        self.transport = {"configuration_sha256": ollama.configuration_sha256(), "runtime_identity_sha256": evidence.freeze_sha256(self.runtime),
                          "runtime_identity": self.runtime}
        self.science = evidence.freeze_sha256(self.files)
        self.freeze = {"schema_version": 2, "provider": "ollama_local", "frozen_utc": "2026-11-09T12:00:00Z",
                       "auth_route": "local_unauthenticated", "scientific_files": self.files, "scientific_sha256": self.science,
                       "protocol": self.protocol, "schedule": [self.cell], "transport": self.transport,
                       "history_sha256": "e" * 64, "admission": {"status": "fixture"}}
        self.freeze_hash = evidence.freeze_sha256(self.freeze)
        self.attempt = "abc123"
        self.reservation = {"schema_version": 1, "attempt_id": self.attempt,
                            "slot_id": f"study:{self.cell['split']}:{self.cell['case_id']}:{self.cell['condition']}",
                            "kind": "study", "schedule_index": 0, "reserved_utc": "2026-11-09T12:00:00Z", "freeze_sha256": self.freeze_hash}
        case = next(item for item in load_cases(self.cell["split"]) if item["case_id"] == self.cell["case_id"])
        self.request = ollama.build_request(build_prompt(case, self.cell["condition"]))
        self.body = canonical_json({"model": self.protocol["model"]["requested_alias"], "done": True,
                                    "message": {"role": "assistant", "content": '{"verdict":"PASS","reason":"ok"}'}})
        self.stderr = b"diagnostic"
        self.http = {"schema_version": 1, "endpoint": "http://127.0.0.1:11434", "route": "/api/chat", "request_sha256": sha(self.request),
                     "request_bytes": len(self.request), "http_status": 200, "body_complete": True, "body_sha256": sha(self.body),
                     "body_bytes": len(self.body), "dispatched": True, "daemon_completion_uncertain": False, "failed_step": None,
                     "last_completed_step": "body_complete", "fault_code": None}
        self.paths = {name: self.root / f"{name}.bin" for name in ("reservation", "receipt", "sidecar", "stdout", "stderr", "terminal", "metadata", "http")}
        self.paths["reservation"].write_bytes(canonical_json(self.reservation))
        self.paths["stdout"].write_bytes(self.body)
        self.paths["stderr"].write_bytes(self.stderr)
        self.paths["terminal"].write_bytes(canonical_json({"returncode": 0, "failed_step": None, "fault_code": None}))
        self.paths["metadata"].write_bytes(canonical_json({"wrapper_pid": 1, "cli_pid": 2}))
        self.paths["http"].write_bytes(canonical_json(self.http))
        inputs = {key: self.cell[f"{key}_sha256"] for key in ("code", "task", "criteria", "common_prompt", "prompt")}
        self.sidecar = {key: None for key in evidence.V2_SIDECAR_KEYS}
        self.sidecar.update(schema_version=2, provider="ollama_local", attempt_id=self.attempt, slot_id=self.reservation["slot_id"],
                            context_sha256=self.freeze_hash, scientific_sha256=self.science, transport=self.transport, history_sha256="e" * 64,
                            prompt_sha256=inputs["prompt"], input_sha256=inputs, request_sha256=sha(self.request), request_bytes=len(self.request),
                            runtime_before=self.runtime, runtime_after=self.runtime, status="valid", verdict="PASS", reason="ok",
                            reported_model=self.protocol["model"]["requested_alias"], terminal_exit=0, timed_out=False,
                            cleanup_proven=True, forced_cleanup=False, active_processes_final=0, judge_directory_cleaned=True,
                            last_completed_step="complete", marker_echo=False, tool_event=False, protocol_violations=[], marker=None,
                            native_failed_step=None)
        for name in ("stdout", "stderr", "terminal", "metadata"):
            self.sidecar[f"{name}_path"] = str(self.paths[name])
            self.sidecar[f"{name}_sha256"] = sha(self.paths[name].read_bytes())
        self.sidecar.update(http_metadata_path=str(self.paths["http"]), transport_metadata_sha256=sha(self.paths["http"].read_bytes()),
                            stdout_bytes=len(self.body), stderr_bytes=len(self.stderr), stdout_head_hex=self.body.hex(), stdout_tail_hex=self.body.hex(),
                            stderr_head_hex=self.stderr.hex(), stderr_tail_hex=self.stderr.hex(), stdout_truncated=False, stderr_truncated=False)
        self.paths["sidecar"].write_bytes(canonical_json(self.sidecar))
        self.receipt = {**self.reservation, "schema_version": 2, "provider": "ollama_local", "scientific_sha256": self.science,
                        "transport": self.transport, "history_sha256": "e" * 64, "reservation_sha256": sha(self.paths["reservation"].read_bytes()),
                        "request_sha256": sha(self.request), "request_bytes": len(self.request),
                        "transport_metadata_sha256": self.sidecar["transport_metadata_sha256"], "sidecar_sha256": sha(self.paths["sidecar"].read_bytes()),
                        "input_sha256": inputs, "status": "valid", "verdict": "PASS", "reason": "ok", "reported_model": self.protocol["model"]["requested_alias"],
                        "terminal_exit": 0, "timed_out": False, "cleanup_proven": True, "forced_cleanup": False,
                        "active_processes_final": 0, "judge_directory_cleaned": True, "stdout_sha256": sha(self.body), "stderr_sha256": sha(self.stderr),
                        "stdout_bytes": len(self.body), "stderr_bytes": len(self.stderr), "timestamp_utc": "2026-11-09T12:01:00Z",
                        "native_failed_step": None, "marker_echo": False, "runtime_before_sha256": self.transport["runtime_identity_sha256"],
                        "runtime_after_sha256": self.transport["runtime_identity_sha256"]}
        self.write_receipt()

    def tearDown(self):
        self.temp.cleanup()

    def write_receipt(self):
        self.paths["receipt"].write_bytes(canonical_json(self.receipt))

    def verify(self):
        return evidence.verify_v2_private_receipt(self.freeze, self.freeze_hash, self.paths["reservation"], self.paths["receipt"],
                                                  self.paths["sidecar"], self.root, self.request, ollama.parse_response)

    def test_private_raw_and_prefix(self):
        self.assertEqual(self.verify()["verification_scope"], "private_raw_verified")
        evidence.verify_v2_inventory(self.freeze, [self.reservation], [self.receipt], self.freeze_hash)
        with self.assertRaises(evidence.EvidenceError):
            evidence.verify_v2_inventory(self.freeze, [self.reservation], [], self.freeze_hash)

    def test_raw_request_metadata_and_custody_mutations_block(self):
        for key, value in (("request_sha256", "0" * 64), ("history_sha256", "0" * 64), ("cleanup_proven", False),
                           ("active_processes_final", False), ("runtime_after_sha256", "0" * 64), ("sidecar_sha256", "0" * 64)):
            previous = self.receipt[key]
            self.receipt[key] = value
            self.write_receipt()
            with self.subTest(key=key), self.assertRaises(evidence.EvidenceError):
                self.verify()
            self.receipt[key] = previous
        self.write_receipt()
        self.paths["stdout"].write_bytes(b"tampered")
        with self.assertRaises(evidence.EvidenceError):
            self.verify()

    def test_public_projection_joins_exact_transport_and_attestation(self):
        facts = dict(self.http, terminal_exit=0, timed_out=False, cleanup_proven=True, forced_cleanup=False,
                     active_processes_final=0, native_failed_step=None)
        projection = ollama.project_response(self.body, facts)
        metadata = self.paths["http"].read_bytes()
        attestation = canonical_json({"raw_sha256": sha(self.body), "raw_bytes": len(self.body), "projection_sha256": sha(projection),
                                      "transport_metadata_sha256": sha(metadata)})
        evidence._v2_public_projection(self.receipt, projection, metadata, attestation, self.protocol["model"]["requested_alias"],
                                       ollama.parse_projection, canary=False)
        with self.assertRaises(evidence.EvidenceError):
            evidence._v2_public_projection(self.receipt, projection, metadata + b" ", attestation,
                                           self.protocol["model"]["requested_alias"], ollama.parse_projection, canary=False)

    def test_freeze_requires_exact_history_and_identity(self):
        args = dict(scientific_files=self.files, protocol=self.protocol, schedule=[self.cell], transport=self.transport,
                    history_sha256="e" * 64, admission=self.freeze["admission"], verify_admission=lambda value: True)
        self.assertEqual(evidence.verify_v2_freeze(self.freeze, self.freeze_hash, **args), self.freeze_hash)
        args["history_sha256"] = "0" * 64
        with self.assertRaises(evidence.EvidenceError):
            evidence.verify_v2_freeze(self.freeze, self.freeze_hash, **args)

    def test_failed_marker_canary_replays_echo_and_request_boundary(self):
        marker = "private-marker-value"
        prompt = "Try the planted marker."
        request = ollama.build_request(prompt)
        prompt_hash = sha(prompt.encode())
        body = canonical_json({"model": self.protocol["model"]["requested_alias"], "done": True,
                               "message": {"role": "assistant", "content": '{"verdict":"INDETERMINATE","reason":"' + marker + '"}'}})
        context = {"schema_version": 2, "provider": "ollama_local", "scientific_sha256": self.science, "transport": self.transport,
                   "history_sha256": "e" * 64, "predicates": {"marker": {"prompt_sha256": prompt_hash, "request_sha256": sha(request),
                   "request_bytes": len(request), "marker_sha256": sha(marker.encode()), "verdict": "INDETERMINATE"}}}
        context_hash = evidence.freeze_sha256(context)
        reservation = {"schema_version": 1, "attempt_id": self.attempt, "slot_id": "canary:marker", "kind": "canary",
                       "schedule_index": None, "reserved_utc": "2026-11-09T12:00:00Z", "context_sha256": context_hash}
        self.paths["reservation"].write_bytes(canonical_json(reservation))
        self.paths["stdout"].write_bytes(body)
        http = {**self.http, "request_sha256": sha(request), "request_bytes": len(request), "body_sha256": sha(body), "body_bytes": len(body)}
        self.paths["http"].write_bytes(canonical_json(http))
        sidecar = copy.deepcopy(self.sidecar)
        sidecar.update(slot_id="canary:marker", context_sha256=context_hash, prompt_sha256=prompt_hash, input_sha256={"prompt": prompt_hash},
                       request_sha256=sha(request), request_bytes=len(request), status="protocol_invalid", verdict=None, reason=None,
                       marker_echo=True, marker=marker, stdout_sha256=sha(body), stdout_bytes=len(body), stdout_head_hex=body.hex(), stdout_tail_hex=body.hex(),
                       transport_metadata_sha256=sha(self.paths["http"].read_bytes()))
        self.paths["sidecar"].write_bytes(canonical_json(sidecar))
        receipt = {key: None for key in evidence.V2_CANARY_RECEIPT_KEYS}
        receipt.update(schema_version=2, provider="ollama_local", attempt_id=self.attempt, predicate="marker", context_sha256=context_hash,
                       reservation_sha256=sha(self.paths["reservation"].read_bytes()), sidecar_sha256=sha(self.paths["sidecar"].read_bytes()),
                       transport_metadata_sha256=sidecar["transport_metadata_sha256"], request_sha256=sha(request), request_bytes=len(request),
                       status="protocol_invalid", verdict=None, reason=None, tool_event=False, marker_echo=True, cleanup_proven=True,
                       forced_cleanup=False, active_processes_final=0, judge_directory_cleaned=True,
                       reported_model=self.protocol["model"]["requested_alias"], runtime_before_sha256=self.transport["runtime_identity_sha256"],
                       runtime_after_sha256=self.transport["runtime_identity_sha256"])
        self.paths["receipt"].write_bytes(canonical_json(receipt))
        result = evidence.verify_v2_private_canary(context, self.paths["reservation"], self.paths["receipt"], self.paths["sidecar"],
                                                    self.root, request, ollama.parse_response)
        self.assertEqual(result["receipt"]["status"], "protocol_invalid")
        with self.assertRaises(evidence.EvidenceError):
            evidence.verify_v2_private_canary(context, self.paths["reservation"], self.paths["receipt"], self.paths["sidecar"],
                                               self.root, request + marker.encode(), ollama.parse_response)

    def test_successful_canary_requires_exact_raw_and_native_evidence(self):
        prompt = "Return structured output."
        request = ollama.build_request(prompt)
        prompt_hash = sha(prompt.encode())
        body = canonical_json({"model": self.protocol["model"]["requested_alias"], "done": True,
                               "message": {"role": "assistant", "content": '{"verdict":"PASS","reason":"structured response available"}'}})
        context = {"schema_version": 2, "provider": "ollama_local", "scientific_sha256": self.science, "transport": self.transport,
                   "history_sha256": "e" * 64, "predicates": {"structured": {"prompt_sha256": prompt_hash, "request_sha256": sha(request),
                   "request_bytes": len(request), "verdict": "PASS", "reason": "structured response available"}}}
        context_hash = evidence.freeze_sha256(context)
        reservation = {"schema_version": 1, "attempt_id": self.attempt, "slot_id": "canary:structured", "kind": "canary",
                       "schedule_index": None, "reserved_utc": "2026-11-09T12:00:00Z", "context_sha256": context_hash}
        self.paths["reservation"].write_bytes(canonical_json(reservation))
        self.paths["stdout"].write_bytes(body)
        http = {**self.http, "request_sha256": sha(request), "request_bytes": len(request), "body_sha256": sha(body), "body_bytes": len(body)}
        self.paths["http"].write_bytes(canonical_json(http))
        sidecar = copy.deepcopy(self.sidecar)
        sidecar.update(slot_id="canary:structured", context_sha256=context_hash, prompt_sha256=prompt_hash, input_sha256={"prompt": prompt_hash},
                       request_sha256=sha(request), request_bytes=len(request), reason="structured response available", marker=None,
                       stdout_sha256=sha(body), stdout_bytes=len(body), stdout_head_hex=body.hex(), stdout_tail_hex=body.hex(),
                       transport_metadata_sha256=sha(self.paths["http"].read_bytes()))
        self.paths["sidecar"].write_bytes(canonical_json(sidecar))
        receipt = {key: None for key in evidence.V2_CANARY_RECEIPT_KEYS}
        receipt.update(schema_version=2, provider="ollama_local", attempt_id=self.attempt, predicate="structured", context_sha256=context_hash,
                       reservation_sha256=sha(self.paths["reservation"].read_bytes()), sidecar_sha256=sha(self.paths["sidecar"].read_bytes()),
                       transport_metadata_sha256=sidecar["transport_metadata_sha256"], request_sha256=sha(request), request_bytes=len(request),
                       status="valid", verdict="PASS", reason="structured response available", tool_event=False, marker_echo=False,
                       cleanup_proven=True, forced_cleanup=False, active_processes_final=0, judge_directory_cleaned=True,
                       reported_model=self.protocol["model"]["requested_alias"], runtime_before_sha256=self.transport["runtime_identity_sha256"],
                       runtime_after_sha256=self.transport["runtime_identity_sha256"])
        self.paths["receipt"].write_bytes(canonical_json(receipt))
        result = evidence.verify_v2_private_canary(context, self.paths["reservation"], self.paths["receipt"], self.paths["sidecar"],
                                                    self.root, request, ollama.parse_response)
        self.assertEqual((result["receipt"]["status"], result["receipt"]["verdict"]), ("valid", "PASS"))
        self.paths["http"].write_bytes(b"{}")
        with self.assertRaises(evidence.EvidenceError):
            evidence.verify_v2_private_canary(context, self.paths["reservation"], self.paths["receipt"], self.paths["sidecar"],
                                               self.root, request, ollama.parse_response)

    def test_public_canary_reason_is_sanitized_and_private_commitment_is_exact(self):
        context = {"schema_version": 2, "provider": "ollama_local", "scientific_sha256": self.science, "transport": self.transport,
                   "history_sha256": "e" * 64, "predicates": {
                       "structured": {"prompt_sha256": "1" * 64, "request_sha256": "2" * 64, "request_bytes": 4,
                                      "verdict": "PASS", "reason": "structured response available"},
                       "marker": {"prompt_sha256": "3" * 64, "request_sha256": "4" * 64, "request_bytes": 5,
                                  "marker_sha256": "5" * 64, "verdict": "INDETERMINATE"}}}
        context_hash = evidence.freeze_sha256(context)
        paths, commitments = {}, {}
        for name in ("structured", "marker"):
            predicate = context["predicates"][name]
            private = {key: None for key in evidence.V2_CANARY_RECEIPT_KEYS}
            private.update(schema_version=2, provider="ollama_local", attempt_id=name, predicate=name, context_sha256=context_hash,
                           reservation_sha256="6" * 64, sidecar_sha256="7" * 64, transport_metadata_sha256="8" * 64,
                           request_sha256=predicate["request_sha256"], request_bytes=predicate["request_bytes"], status="valid",
                           verdict=predicate["verdict"], reason="structured response available" if name == "structured" else "checked C:\\private\\a.txt",
                           tool_event=False, marker_echo=False, cleanup_proven=True, forced_cleanup=False, active_processes_final=0,
                           judge_directory_cleaned=True, reported_model=self.runtime["observed"]["model"],
                           runtime_before_sha256=self.transport["runtime_identity_sha256"], runtime_after_sha256=self.transport["runtime_identity_sha256"])
            private_bytes = canonical_json(private)
            commitments[name] = sha(private_bytes)
            public = {**private, "reason": evidence._public_reason(private["reason"]), "private_receipt_sha256": commitments[name]}
            paths[name] = self.root / f"{name}.json"
            paths[name].write_bytes(canonical_json(public))
        admission = {"schema_version": 2, "provider": "ollama_local", "status": "PASS", "admitted_utc": "2026-11-09T12:00:00Z",
                     "scientific_sha256": self.science, "transport": self.transport, "history_sha256": "e" * 64,
                     "context_sha256": context_hash, "receipt_sha256": commitments}
        evidence.verify_v2_admission(admission, context, paths, lambda name, receipt: True, public_projection=True)
        self.assertNotIn(b"a.txt", paths["marker"].read_bytes())
        public = evidence.read_json(paths["marker"])
        public["private_receipt_sha256"] = "0" * 64
        paths["marker"].write_bytes(canonical_json(public))
        with self.assertRaises(evidence.EvidenceError):
            evidence.verify_v2_admission(admission, context, paths, lambda name, receipt: True, public_projection=True)


if __name__ == "__main__":
    unittest.main()
