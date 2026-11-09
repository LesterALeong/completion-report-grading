import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from study import codex_cli, evidence, runner
from study.analysis import analyze, load_verified_bundle
from study.export import export_public_bundle
from study.protocol import TASK_TMP
from study.windows_job import run_native


@unittest.skipUnless(os.name == "nt", "native producer integration requires Windows")
class ExportIntegrationTests(unittest.TestCase):
    def setUp(self):
        TASK_TMP.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="portable-export-", dir=TASK_TMP)
        self.root = Path(self.temporary.name)
        self.private = self.root / "private"
        self.private.mkdir()
        self.target = self.root / "public"
        self.active = []
        paths = {"TASK_TMP": self.private, "PREFLIGHT_PATH": self.private / "preflight.json", "FREEZE_PATH": self.private / "freeze.json",
                 "CANARY_PATH": self.private / "canary-summary.json", "RESERVATION_DIR": self.private / "reservations",
                 "RECEIPT_DIR": self.private / "receipts", "SIDECAR_DIR": self.private / "sidecars",
                 "CANARY_RUN_DIR": self.private / "canary-runs", "JUDGE_DIR": self.private / "judge", "LOCK_PATH": self.private / "operator.lock"}
        for key, value in paths.items():
            self.install(patch.object(runner, key, value))
        legacy_path = Path(__file__).resolve().parents[1] / "docs" / "protocols" / "codex-v1.json"
        legacy_protocol = json.loads(legacy_path.read_text(encoding="utf-8"))
        self.install(patch.object(runner, "load_protocol", return_value=legacy_protocol))
        self.install(patch.object(codex_cli, "load_protocol", return_value=legacy_protocol))
        self.cli = {"version": "inert", "binary_sha256": "1" * 64,
                    "configuration_sha256": codex_cli.configuration_sha256(), "version_check_passed": True}
        self.install(patch.object(codex_cli, "inspect_cli", side_effect=lambda: dict(self.cli)))
        self.install(patch.object(codex_cli, "chatgpt_login_status", return_value=True))
        self.install(patch.object(codex_cli, "run_codex", side_effect=self.inert_transport))
        self.wrong_canary = True
        self.study_stdout = None
        self.calls = 0
        runner.ensure_task_dirs()
        self.write_preflight()

    def install(self, active):
        active.start()
        self.active.append(active)

    def tearDown(self):
        for active in reversed(self.active):
            active.stop()
        self.temporary.cleanup()

    def write_preflight(self):
        files = evidence.scientific_closure(runner.REPO_ROOT)
        runner._save_json(runner.PREFLIGHT_PATH, {"status": "PASS", "auth_route": "chatgpt_subscription", "cli": dict(self.cli),
                          "scientific_files": files, "scientific_sha256": evidence.freeze_sha256(files)})

    def inert_transport(self, prompt, cwd, timeout, marker=None):
        self.calls += 1
        directory = self.private / "captures" / str(self.calls)
        directory.mkdir(parents=True)
        if prompt in {runner.STRUCTURED_PROMPT, runner.MARKER_PROMPT}:
            verdict = "INDETERMINATE" if marker else "PASS"
            reason = "no access" if marker else ("wrong" if self.wrong_canary else "structured response available")
            events = [{"type": "thread.started", "thread_id": "SECRET-THREAD-ID"}, {"type": "turn.started"},
                      {"type": "item.completed", "item": {"id": "SECRET-ITEM-ID", "type": "agent_message",
                                                               "text": json.dumps({"verdict": verdict, "reason": reason})}},
                      {"type": "turn.completed", "model": "backend"}]
            stdout_data = ("\n".join(map(json.dumps, events)) + "\n").encode()
        else:
            stdout_data = self.study_stdout or b'{"type":"thread.started"}\n{"type":"turn.started"}\n{bad private json\n'
        source = ("import sys;sys.stdout.buffer.write(bytes.fromhex('" + stdout_data.hex() +
                  "'));sys.stderr.buffer.write(bytes.fromhex('" + b"SECRET-PRIVATE-STDERR".hex() + "'))")
        native = run_native([sys.executable, "-I", "-S", "-B", "-c", source], prompt, cwd, directory, timeout)
        self.assertTrue(native.cleanup_proven)
        self.assertFalse(native.forced_cleanup)
        stdout, stderr = native.stdout_path, native.stderr_path
        terminal, metadata = native.terminal_path, native.metadata_path
        parsed = codex_cli.parse_event_stream(stdout_data.decode(), 0)
        out_capture, _, _ = codex_cli._capture(stdout, None, True)
        err_capture, _, _ = codex_cli._capture(stderr, None, False)
        return codex_cli.ProcessResult(parsed.status, parsed.verdict, parsed.reason, 0, False, parsed.reported_model,
                                       parsed.event_count, True, False, 0, None, "terminal_read", None,
                                       stdout, stderr, terminal, metadata, out_capture, err_capture,
                                       parsed.protocol_violations, parsed.tool_event, False)

    def prepare(self):
        self.assertEqual(runner.run_canaries(True, True)["status"], "BLOCKED")
        self.cli["binary_sha256"] = "2" * 64
        self.write_preflight()
        self.wrong_canary = False
        self.assertEqual(runner.run_canaries(True, True, changed_premise="inert binary identity changed")["status"], "PASS")
        runner.freeze_protocol()
        self.assertEqual(runner.run_split("development", True)["status"], "BLOCKED")

    def test_real_export_public_replay_and_clean_cli(self):
        self.prepare()
        result = export_public_bundle(self.private, self.target)
        self.assertEqual((result["status"], result["study_attempts"], result["canary_attempts"]), ("PASS", 1, 3))
        with self.assertRaises(FileExistsError):
            export_public_bundle(self.private, self.target)
        for path in self.target.rglob("*"):
            if path.is_file():
                data = path.read_bytes()
                for secret in (b"SECRET-THREAD-ID", b"SECRET-ITEM-ID", b"SECRET-PRIVATE-STDERR", str(self.private).encode()):
                    self.assertNotIn(secret, data)
        shutil.rmtree(self.private)
        bundle = load_verified_bundle(self.target, scope="public_projection_replay", manifest_sha256=result["manifest_sha256"])
        report = analyze("development", bundle)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["verification_scope"], "public_projection_replay")
        self.assertEqual(report["valid_cells"], 0)
        env = os.environ.copy()
        env["PATH"] = ""
        env.pop("PYTHONPATH", None)
        env["COMPLETION_REPORT_TMP"] = str(self.root / "absent-private")
        for name in codex_cli.API_ROUTE_ENVIRONMENT:
            env.pop(name, None)
        for name in ("CODEX_HOME", "HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA"):
            env[name] = str(self.root / "no-auth-profile")
        completed = subprocess.run([sys.executable, "-S", "-B", "-m", "study", "analyze", "--split", "development",
                                    "--bundle", str(self.target), "--scope", "public_projection_replay", "--manifest-sha256", result["manifest_sha256"]],
                                   cwd=str(runner.REPO_ROOT), env=env, capture_output=True, text=True, timeout=30, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["verification_scope"], "public_projection_replay")
        bad_manifest = load_verified_bundle(self.target, scope="public_projection_replay", manifest_sha256="0" * 64)
        self.assertEqual(analyze("development", bad_manifest)["status"], "BLOCKED")
        projection = next((self.target / "projections").glob("*.jsonl"))
        projection.write_bytes(b"tampered")
        blocked = load_verified_bundle(self.target, scope="public_projection_replay", manifest_sha256=result["manifest_sha256"])
        self.assertEqual(analyze("development", blocked)["status"], "BLOCKED")

    def test_missing_private_raw_blocks_before_target_creation(self):
        self.prepare()
        receipt = runner.load_private_bundle(self.private)["receipts"][0]
        sidecar = runner._read_json(runner.SIDECAR_DIR / f"{receipt['attempt_id']}.json")
        Path(sidecar["stdout_path"]).unlink()
        with self.assertRaises(evidence.EvidenceError):
            export_public_bundle(self.private, self.target)
        self.assertFalse(self.target.exists())

    def test_private_source_cli_and_custody_drift_block_export(self):
        self.prepare()
        with patch.object(evidence, "scientific_closure", return_value={}):
            with self.assertRaises(evidence.EvidenceError):
                export_public_bundle(self.private, self.target)
        with patch.object(codex_cli, "configuration_sha256", return_value="0" * 64):
            with self.assertRaises(evidence.EvidenceError):
                export_public_bundle(self.private, self.target)
        receipt = runner.load_private_bundle(self.private)["receipts"][0]
        sidecar_path = runner.SIDECAR_DIR / f"{receipt['attempt_id']}.json"
        sidecar = runner._read_json(sidecar_path)
        sidecar["cleanup_proven"] = False
        runner._save_json(sidecar_path, sidecar)
        with self.assertRaises(evidence.EvidenceError):
            export_public_bundle(self.private, self.target)
        self.assertFalse(self.target.exists())

    def _duplicate_key_runner_export(self, stdout, expected_status):
        self.study_stdout = stdout
        self.prepare()
        private = runner.load_private_bundle(self.private)
        self.assertEqual((private["receipts"][0]["status"], private["receipts"][0]["verdict"]), (expected_status, None))
        exported = export_public_bundle(self.private, self.target)
        bundle = load_verified_bundle(self.target, scope="public_projection_replay", manifest_sha256=exported["manifest_sha256"])
        report = analyze("development", bundle)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["valid_cells"], 0)
        self.assertEqual(sum(cell["status"] == expected_status for cell in report["cells"]), 1)

    def test_duplicate_final_key_remains_invalid_through_runner_export(self):
        final = '{"verdict":"FAIL","verdict":"PASS","reason":"checked"}'
        events = [{"type": "thread.started"}, {"type": "turn.started"},
                  {"type": "item.completed", "item": {"type": "agent_message", "text": final}},
                  {"type": "turn.completed"}]
        self._duplicate_key_runner_export(("\n".join(map(json.dumps, events)) + "\n").encode(), "invalid_output")

    def test_duplicate_envelope_type_remains_invalid_through_runner_export(self):
        final = json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": '{"verdict":"PASS","reason":"checked"}'}})
        raw = ('{"type":"thread.started"}\n{"type":"turn.started"}\n' + final +
               '\n{"type":"error","type":"turn.completed"}\n').encode()
        self._duplicate_key_runner_export(raw, "protocol_invalid")


if __name__ == "__main__":
    unittest.main()
