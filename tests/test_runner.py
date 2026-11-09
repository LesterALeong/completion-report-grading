import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from study import codex_cli, evidence, runner
from study.protocol import TASK_TMP, sha256_bytes


class RunnerTests(unittest.TestCase):
    def setUp(self):
        TASK_TMP.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="runner-inert-", dir=TASK_TMP)
        self.root = Path(self.temp.name)
        self.patches = []
        mapping = {"TASK_TMP": self.root, "PREFLIGHT_PATH": self.root / "preflight.json",
                   "FREEZE_PATH": self.root / "freeze.json", "CANARY_PATH": self.root / "canary-summary.json",
                   "RESERVATION_DIR": self.root / "reservations", "RECEIPT_DIR": self.root / "receipts",
                   "SIDECAR_DIR": self.root / "sidecars", "CANARY_RUN_DIR": self.root / "canary-runs",
                   "JUDGE_DIR": self.root / "judge", "LOCK_PATH": self.root / "operator.lock"}
        for name, value in mapping.items():
            self.install(patch.object(runner, name, value))
        self.files = {"study/a.py": "a" * 64, "docs/SPEC.md": "b" * 64}
        self.install(patch.object(evidence, "scientific_closure", side_effect=lambda root: dict(self.files)))
        self.protocol = {"model": {"requested_alias": "alias", "reasoning_effort": "medium"},
                         "turn_budget": {"study": 2, "canary": 4, "absolute": 6}, "cli": {"timeout_seconds": 5}}
        self.install(patch.object(runner, "load_protocol", return_value=self.protocol))
        self.cli = {"version": "inert", "binary_sha256": "1" * 64, "configuration_sha256": "2" * 64, "version_check_passed": True}
        self.install(patch.object(codex_cli, "inspect_cli", side_effect=lambda: dict(self.cli)))
        self.install(patch.object(codex_cli, "configuration_sha256", side_effect=lambda: self.cli["configuration_sha256"]))
        self.install(patch.object(codex_cli, "chatgpt_login_status", return_value=True))
        self.cases = {"development": [{"case_id": "D01"}], "holdout": [{"case_id": "H01"}]}
        self.install(patch.object(runner, "load_cases", side_effect=lambda split: self.cases[split]))
        self.install(patch.object(runner, "build_prompt", side_effect=lambda case, condition: f"prompt-{case['case_id']}"))
        self.schedule = []
        for split, case_id in (("development", "D01"), ("holdout", "H01")):
            cell = {"split": split, "case_id": case_id, "condition": "neutral"}
            cell.update({f"{name}_sha256": sha256_bytes(name.encode()) for name in ("code", "task", "criteria", "common_prompt")})
            cell["prompt_sha256"] = sha256_bytes(f"prompt-{case_id}".encode())
            self.schedule.append(cell)
        self.install(patch.object(runner, "ordered_schedule", side_effect=lambda: self.schedule))
        self.wrong = False
        self.wrong_marker = False
        self.leak_marker = False
        self.backend = "backend"
        self.calls = []
        self.install(patch.object(codex_cli, "run_codex", side_effect=self.inert_transport))
        runner.ensure_task_dirs()
        self.write_preflight()

    def install(self, active):
        active.start()
        self.patches.append(active)

    def tearDown(self):
        for active in reversed(self.patches):
            active.stop()
        self.temp.cleanup()

    def write_preflight(self):
        runner._save_json(runner.PREFLIGHT_PATH, {"status": "PASS", "auth_route": "chatgpt_subscription", "cli": dict(self.cli),
                          "scientific_files": dict(self.files), "scientific_sha256": evidence.freeze_sha256(self.files)})

    def inert_transport(self, prompt, cwd, timeout, marker=None):
        self.calls.append(prompt)
        directory = self.root / "captures" / str(len(self.calls))
        directory.mkdir(parents=True)
        verdict = ("PASS" if self.wrong_marker else "INDETERMINATE") if marker else "PASS"
        reason = "no access" if marker else ("incorrect" if self.wrong and prompt == runner.STRUCTURED_PROMPT else
                                              "structured response available" if prompt == runner.STRUCTURED_PROMPT else "checked")
        events = [{"type": "thread.started"}, {"type": "turn.started"},
                  {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps({"verdict": verdict, "reason": reason})}},
                  {"type": "turn.completed", "model": self.backend}]
        stdout = directory / "stdout.bin"
        stderr = directory / "stderr.bin"
        terminal = directory / "terminal.json"
        metadata = directory / "process.json"
        stdout.write_text("\n".join(map(json.dumps, events)) + "\n", encoding="utf-8")
        stderr.write_bytes(marker.encode() if marker and self.leak_marker else b"")
        terminal.write_text(json.dumps({"returncode": 0, "failed_step": None, "fault_code": None}), encoding="utf-8")
        metadata.write_text(json.dumps({"wrapper_pid": 101, "cli_pid": 102}), encoding="utf-8")
        out_capture, _, _ = codex_cli._capture(stdout, None, True)
        err_capture, _, _ = codex_cli._capture(stderr, None, False)
        return codex_cli.ProcessResult("valid", verdict, reason, 0, False, self.backend, len(events), True, False, 0,
                                       None, "terminal_read", None, stdout, stderr, terminal, metadata,
                                       out_capture, err_capture, (), False, False)

    def test_authorization_refusals(self):
        with self.assertRaisesRegex(RuntimeError, "authorize-subscription-calls"):
            runner.run_split("development", False)
        with self.assertRaisesRegex(RuntimeError, "explicit subscription-call authorization"):
            runner.run_canaries(False, False)

    def test_actual_callers_canary_freeze_and_study_resume(self):
        self.assertEqual(runner.run_canaries(True, True)["status"], "PASS")
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(runner.run_canaries(True, True)["status"], "PASS")
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(runner.freeze_protocol()["status"], "PASS")
        self.assertEqual(runner.run_split("development", True)["status"], "PASS")
        self.assertEqual(runner.run_split("holdout", True)["status"], "PASS")
        bundle = runner.load_private_bundle(self.root)
        self.assertEqual(bundle["verification_scope"], "private_raw_verified")
        self.assertEqual(len(bundle["receipts"]), 2)
        self.assertEqual(len(self.calls), 4)
        with self.assertRaises(RuntimeError):
            runner.run_canaries(True, True)

    def test_canary_predicate_failure_requires_changed_source_or_config(self):
        self.wrong = True
        self.assertEqual(runner.run_canaries(True, True)["status"], "BLOCKED")
        self.assertEqual(len(self.calls), 1)
        with self.assertRaisesRegex(RuntimeError, "changed-premise"):
            runner.run_canaries(True, True)
        with self.assertRaisesRegex(RuntimeError, "unchanged"):
            runner.run_canaries(True, True, changed_premise="try again")
        self.cli["configuration_sha256"] = "3" * 64
        self.write_preflight()
        self.wrong = False
        self.assertEqual(runner.run_canaries(True, True, changed_premise="configuration repaired")["status"], "PASS")
        self.assertEqual(runner._counts()["canary"], 3)

    def test_wrong_marker_predicate_and_raw_marker_echo_block(self):
        self.wrong_marker = True
        self.assertEqual(runner.run_canaries(True, True)["status"], "BLOCKED")
        self.assertEqual(len(self.calls), 2)
        self.cli["configuration_sha256"] = "3" * 64
        self.write_preflight()
        self.wrong_marker = False
        self.leak_marker = True
        with self.assertRaises(evidence.EvidenceError):
            runner.run_canaries(True, True, changed_premise="configuration repaired")
        self.assertFalse(runner.CANARY_PATH.exists())
        self.assertEqual(runner._counts()["canary"], 4)

    def test_canary_capacity_requires_both_predicates(self):
        self.protocol["turn_budget"]["canary"] = 1
        with self.assertRaisesRegex(RuntimeError, "insufficient allowance"):
            runner.run_canaries(True, True)
        self.assertEqual(self.calls, [])

    def test_setup_failure_is_durable_and_blocks_resume(self):
        with patch.object(runner, "_new_judge_directory", side_effect=RuntimeError("inert setup")):
            receipt = runner._execute_reserved_call("study:development:D01:neutral", "study", "prompt-D01",
                                                   sha256_bytes(b"prompt-D01"), {}, self.cli, identity_before=None,
                                                   context_sha256="a" * 64, schedule_index=0, scientific_sha256="b" * 64)
        self.assertEqual(receipt["status"], "operational_unknown")
        sidecar = runner._read_json(runner.SIDECAR_DIR / f"{receipt['attempt_id']}.json")
        self.assertEqual((sidecar["failed_step"], sidecar["fault_code"]), ("create_judge", "RuntimeError"))
        self.assertEqual(runner._counts()["study"], 1)

    def test_real_study_caller_persists_setup_failure_without_retry(self):
        runner.run_canaries(True, True)
        runner.freeze_protocol()
        with patch.object(runner, "_new_judge_directory", side_effect=RuntimeError("inert setup")):
            result = runner.run_split("development", True)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(len(self.calls), 2)
        reservations = [item for item in runner._records(runner.RESERVATION_DIR).values() if item["kind"] == "study"]
        self.assertEqual(len(reservations), 1)
        receipt = runner._read_json(runner.RECEIPT_DIR / f"{reservations[0]['attempt_id']}.json")
        sidecar = runner._read_json(runner.SIDECAR_DIR / f"{receipt['attempt_id']}.json")
        self.assertEqual((sidecar["failed_step"], sidecar["fault_code"]), ("create_judge", "RuntimeError"))
        with self.assertRaises(evidence.EvidenceError):
            runner.run_split("development", True)
        self.assertEqual(len(self.calls), 2)

    def test_missing_receipt_corrupt_ledger_and_lock_block(self):
        runner.LOCK_PATH.write_text("owned", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            runner.run_canaries(True, True)
        runner.LOCK_PATH.unlink()
        (runner.RESERVATION_DIR / "bad.json").write_text("{", encoding="utf-8")
        with self.assertRaises(evidence.EvidenceError):
            runner.run_canaries(True, True)
        (runner.RESERVATION_DIR / "bad.json").unlink()
        runner.run_canaries(True, True)
        next(runner.RECEIPT_DIR.glob("*.json")).unlink()
        with self.assertRaises(evidence.EvidenceError):
            runner.run_canaries(True, True)

    def test_raw_mutation_blocks_offline_reducer_and_resume(self):
        runner.run_canaries(True, True)
        runner.freeze_protocol()
        runner.run_split("development", True)
        bundle = runner.load_private_bundle(self.root)
        receipt = bundle["receipts"][0]
        sidecar = runner._read_json(runner.SIDECAR_DIR / f"{receipt['attempt_id']}.json")
        Path(sidecar["stdout_path"]).write_bytes(b"tampered")
        with self.assertRaises(evidence.EvidenceError):
            runner.load_private_bundle(self.root)
        with self.assertRaises(evidence.EvidenceError):
            runner.run_split("holdout", True)

    def test_backend_change_blocks_holdout_without_valid_grade(self):
        runner.run_canaries(True, True)
        runner.freeze_protocol()
        runner.run_split("development", True)
        self.backend = "another-backend"
        result = runner.run_split("holdout", True)
        self.assertEqual(result["status"], "BLOCKED")
        reservation = [record for record in runner._records(runner.RESERVATION_DIR).values() if record["kind"] == "study"]
        last = max(reservation, key=lambda item: item["schedule_index"])
        receipt = runner._read_json(runner.RECEIPT_DIR / f"{last['attempt_id']}.json")
        self.assertEqual(receipt["status"], "operational_unknown")
        self.assertIsNone(receipt["verdict"])
        sidecar = runner._read_json(runner.SIDECAR_DIR / f"{receipt['attempt_id']}.json")
        self.assertEqual((sidecar["failed_step"], sidecar["fault_code"]), ("backend_identity", "BACKEND_CHANGED"))

    def test_stale_admission_and_offline_config_drift_block(self):
        runner.run_canaries(True, True)
        self.files["study/a.py"] = "c" * 64
        self.write_preflight()
        with self.assertRaises(evidence.EvidenceError):
            runner.run_canaries(True, True)
        self.files["study/a.py"] = "a" * 64
        self.write_preflight()
        runner.freeze_protocol()
        self.cli["configuration_sha256"] = "3" * 64
        with self.assertRaises(evidence.EvidenceError):
            runner.load_private_bundle(self.root)

    def test_custody_mutation_cannot_become_valid(self):
        runner.run_canaries(True, True)
        runner.freeze_protocol()
        runner.run_split("development", True)
        receipt = runner.load_private_bundle(self.root)["receipts"][0]
        receipt_path = runner.RECEIPT_DIR / f"{receipt['attempt_id']}.json"
        sidecar_path = runner.SIDECAR_DIR / f"{receipt['attempt_id']}.json"
        sidecar = runner._read_json(sidecar_path)
        sidecar["cleanup_proven"] = False
        runner._save_json(sidecar_path, sidecar)
        receipt["cleanup_proven"] = False
        receipt["sidecar_sha256"] = sha256_bytes(sidecar_path.read_bytes())
        runner._save_json(receipt_path, receipt)
        with self.assertRaises(evidence.EvidenceError):
            runner.load_private_bundle(self.root)


if __name__ == "__main__":
    unittest.main()
