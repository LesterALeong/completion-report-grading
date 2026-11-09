import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from study import codex_cli, evidence, ollama, runner
from study.data import load_protocol
from study.protocol import TASK_TMP, canonical_json, sha256_bytes


class RunnerV2Tests(unittest.TestCase):
    def setUp(self):
        TASK_TMP.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="runner-v2-", dir=TASK_TMP)
        self.root = Path(self.temp.name)
        self.patches = []
        self.install(patch.dict(os.environ))
        for name, value in {"TASK_TMP": self.root, "PREFLIGHT_PATH": self.root / "preflight.json",
                            "FREEZE_PATH": self.root / "freeze.json", "CANARY_PATH": self.root / "canary-summary.json",
                            "RESERVATION_DIR": self.root / "reservations", "RECEIPT_DIR": self.root / "receipts",
                            "SIDECAR_DIR": self.root / "sidecars", "CANARY_RUN_DIR": self.root / "canary-runs",
                            "JUDGE_DIR": self.root / "judge", "LOCK_PATH": self.root / "operator.lock"}.items():
            self.install(patch.object(runner, name, value))
        self.protocol = copy.deepcopy(load_protocol())
        self.protocol["turn_budget"]["study"] = 1
        self.install(patch.object(runner, "load_protocol", return_value=self.protocol))
        original_schedule = runner.ordered_schedule()
        self.schedule = original_schedule[:1]
        self.install(patch.object(runner, "ordered_schedule", return_value=self.schedule))
        self.science = {"study/example.py": "a" * 64}
        self.install(patch.object(evidence, "scientific_closure", return_value=self.science))
        self.install(patch.object(runner, "candidate_files", return_value={}))
        self.install(patch.object(runner, "validate_protocol", return_value={"status": "PASS"}))
        self.runtime = {"endpoint": ollama.ENDPOINT, "observed": self.protocol["transport"]["expected_runtime"],
                        "python_version": "inert", "python_sha256": "b" * 64, "worker_sha256": "c" * 64}
        self.install(patch.object(ollama, "inspect_runtime", side_effect=lambda: copy.deepcopy(self.runtime)))
        self.install(patch.object(ollama, "configuration_sha256", return_value="d" * 64))
        self.history = {"manifest": {"attempts": [{"attempt_id": "a1"}, {"attempt_id": "a2"}]}, "sha256": "e" * 64}
        self.install(patch.object(runner.history, "ensure_history", return_value=self.history))
        self.install(patch.object(runner.history, "verify_history", return_value=self.history))
        self.calls = []
        self.install(patch.object(ollama, "run_ollama", side_effect=self.inert_transport))
        runner.ensure_task_dirs()
        for attempt in ("a1", "a2"):
            reservation = {"schema_version": 1, "attempt_id": attempt, "slot_id": "canary:structured", "kind": "canary",
                           "schedule_index": None, "reserved_utc": runner.utc_now(), "context_sha256": "f" * 64}
            runner._save_json(runner.RESERVATION_DIR / f"{attempt}.json", reservation)
            sidecar_path = runner.SIDECAR_DIR / f"{attempt}.json"
            runner._save_json(sidecar_path, {"attempt_id": attempt})
            runner._save_json(runner.RECEIPT_DIR / f"{attempt}.json", {"attempt_id": attempt, "sidecar_sha256": runner._file_digest(sidecar_path)})
        runner.preflight()

    def install(self, active):
        active.start()
        self.patches.append(active)

    def tearDown(self):
        for active in reversed(self.patches):
            active.stop()
        self.temp.cleanup()

    def inert_transport(self, prompt, cwd, timeout, marker=None):
        self.calls.append(prompt)
        directory = self.root / "captures" / str(len(self.calls))
        directory.mkdir(parents=True)
        verdict = "INDETERMINATE" if marker else "PASS"
        reason = "cannot read" if marker else "structured response available" if prompt == runner.STRUCTURED_PROMPT else "checked"
        body = canonical_json({"model": self.runtime["observed"]["model"], "done": True,
                               "message": {"role": "assistant", "content": json.dumps({"verdict": verdict, "reason": reason})}})
        request = ollama.build_request(prompt)
        http = {"schema_version": 1, "endpoint": ollama.ENDPOINT, "route": "/api/chat", "request_sha256": sha256_bytes(request),
                "request_bytes": len(request), "http_status": 200, "body_complete": True, "body_sha256": sha256_bytes(body),
                "body_bytes": len(body), "dispatched": True, "daemon_completion_uncertain": False, "failed_step": None,
                "last_completed_step": "body_received", "fault_code": None}
        paths = {name: directory / name for name in ("stdout.bin", "stderr.bin", "terminal.json", "process.json", "http.json")}
        paths["stdout.bin"].write_bytes(body)
        paths["stderr.bin"].write_bytes(b"")
        paths["terminal.json"].write_bytes(canonical_json({"returncode": 0, "failed_step": None, "fault_code": None}))
        paths["process.json"].write_bytes(canonical_json({"wrapper_pid": 1, "cli_pid": 2}))
        paths["http.json"].write_bytes(canonical_json(http))
        out, _, _ = codex_cli._capture(paths["stdout.bin"], None, True)
        err, _, _ = codex_cli._capture(paths["stderr.bin"], None, False)
        facts = dict(http, terminal_exit=0, timed_out=False, cleanup_proven=True, forced_cleanup=False,
                     active_processes_final=0, native_failed_step=None)
        return ollama.OllamaResult("valid", verdict, reason, 0, False, self.runtime["observed"]["model"], 0,
                                   True, False, 0, None, "child_exited", None, paths["stdout.bin"], paths["stderr.bin"],
                                   paths["terminal.json"], paths["process.json"], out, err, (), False, False,
                                   paths["http.json"], sha256_bytes(request), len(request), facts)

    def test_callers_and_offline_replay(self):
        self.assertEqual(runner.run_canaries(True, True, "local transport replaces broken Codex route")["status"], "PASS")
        self.assertEqual(runner.freeze_protocol()["status"], "PASS")
        self.assertEqual(runner.run_split("development", True)["status"], "PASS")
        with patch.object(ollama, "inspect_runtime", side_effect=AssertionError("offline replay queried runtime")):
            bundle = runner.load_private_bundle(self.root)
        self.assertEqual(len(bundle["receipts"]), 1)
        self.assertEqual(bundle["canary_reservations"], 4)
        self.assertEqual(bundle["verification_scope"], "private_raw_verified")
        self.assertEqual(len(self.calls), 3)

    def test_setup_failure_consumes_reservation(self):
        with patch.object(runner, "_new_judge_directory", side_effect=RuntimeError("setup")):
            receipt = runner._execute_reserved_call("canary:structured", "canary", runner.STRUCTURED_PROMPT,
                                                   sha256_bytes(runner.STRUCTURED_PROMPT.encode()), {},
                                                   runner._transport_identity(self.runtime), context_sha256="1" * 64,
                                                   scientific_sha256="2" * 64, predicate="structured", history_sha256="e" * 64)
        self.assertEqual(receipt["status"], "operational_unknown")
        self.assertEqual(runner._counts()["canary"], 3)
        self.assertEqual(self.calls, [])

    def test_post_dispatch_drift_stops_and_replays_without_retry(self):
        runner.run_canaries(True, True, "local transport replaces broken Codex route")
        runner.freeze_protocol()
        drifted = copy.deepcopy(self.runtime)
        drifted["worker_sha256"] = "f" * 64
        with patch.object(ollama, "inspect_runtime", side_effect=[copy.deepcopy(self.runtime), drifted]):
            result = runner.run_split("development", True)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["failure_status"], "operational_unknown")
        with patch.object(ollama, "inspect_runtime", side_effect=AssertionError("offline replay queried runtime")):
            bundle = runner.load_private_bundle(self.root)
        self.assertEqual(bundle["receipts"][-1]["status"], "operational_unknown")
        self.assertEqual(runner.run_split("development", True)["new_attempts"], 0)
        self.assertEqual(len(self.calls), 3)

    def test_body_tampering_blocks_offline_replay(self):
        runner.run_canaries(True, True, "local transport replaces broken Codex route")
        runner.freeze_protocol()
        runner.run_split("development", True)
        (self.root / "captures" / "3" / "stdout.bin").write_bytes(b"tampered")
        with self.assertRaises(evidence.EvidenceError):
            runner.load_private_bundle(self.root)


if __name__ == "__main__":
    unittest.main()
