import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from study import history, runner
from study.analysis import BlockedDiagnostic, load_verified_bundle
from study.export import export_public_bundle
from study.protocol import TASK_TMP


class ExportV2IntegrationTests(unittest.TestCase):
    def test_runner_export_public_analysis_and_clean_subprocess(self):
        from tests.test_runner_v2 import RunnerV2Tests

        fixture = RunnerV2Tests("test_callers_and_offline_replay")
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        self.private = fixture.root
        self.target_parent = tempfile.TemporaryDirectory(prefix="export-v2-public-", dir=TASK_TMP)
        self.addCleanup(self.target_parent.cleanup)
        self.target = Path(self.target_parent.name) / "public"
        self._restore_full_protocol_sources_and_history(fixture)

        self.assertEqual(runner.preflight()["status"], "PASS")
        self.assertEqual(runner.run_canaries(True, True, "offline inert replay integration") ["status"], "PASS")
        self.assertEqual(runner.freeze_protocol()["status"], "PASS")
        self.assertEqual(runner.run_split("development", True)["status"], "PASS")
        exported = export_public_bundle(self.private, self.target)
        self.assertEqual((exported["status"], exported["verification_scope"]), ("PASS", "public_projection_replay"))
        self.assertEqual((exported["study_attempts"], exported["canary_attempts"]), (32, 4))
        bundle = load_verified_bundle(self.target, scope="public_projection_replay", manifest_sha256=exported["manifest_sha256"])
        self.assertNotIsInstance(bundle, BlockedDiagnostic)
        self.assertEqual((len(bundle.receipts), len(bundle.canary_reservations), len(bundle.canary_ledger)), (32, 4, 4))
        self.assertEqual(bundle.history_sha256, bundle.freeze["history_sha256"])

        for path in self.target.rglob("*"):
            if path.is_file():
                data = path.read_bytes()
                self.assertNotIn(str(self.private).encode(), data)
                self.assertNotIn(b"stderr_path", data)
                self.assertNotIn(b"stdout_path", data)

        shutil.rmtree(self.private)
        environment = os.environ.copy()
        environment["PATH"] = ""
        environment.pop("PYTHONPATH", None)
        environment["COMPLETION_REPORT_TMP"] = str(self.target_parent.name) + "\\missing-private"
        completed = subprocess.run(
            [sys.executable, "-S", "-B", "-m", "study", "analyze", "--split", "development",
             "--bundle", str(self.target), "--scope", "public_projection_replay",
             "--manifest-sha256", exported["manifest_sha256"]],
            cwd=str(runner.REPO_ROOT), env=environment, capture_output=True, text=True, timeout=60, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        report = json.loads(completed.stdout)
        self.assertEqual((report["status"], report["verification_scope"], report["valid_cells"]),
                         ("PASS", "public_projection_replay", 32))

    def _restore_full_protocol_sources_and_history(self, fixture):
        changed = {"load_protocol", "ordered_schedule", "scientific_closure", "ensure_history", "verify_history"}
        for patcher in list(fixture.patches):
            if getattr(patcher, "attribute", None) in changed:
                patcher.stop()
                fixture.patches.remove(patcher)

        for folder in ("reservations", "receipts", "sidecars"):
            for attempt in ("a1", "a2"):
                path = self.private / folder / f"{attempt}.json"
                if path.exists():
                    path.unlink()

        for index, (attempt, status) in enumerate(zip(history.ATTEMPT_IDS, ("operational_unknown", "protocol_invalid"))):
            context_sha256 = str(index + 1) * 64
            capture_dir = self.private / "historical-captures" / attempt
            capture_dir.mkdir(parents=True)
            captures = {
                "stdout": capture_dir / "stdout.bin",
                "stderr": capture_dir / "stderr.bin",
                "terminal": capture_dir / "terminal.json",
                "metadata": capture_dir / "process.json",
            }
            captures["stdout"].write_bytes(b"retained failed Codex response")
            captures["stderr"].write_bytes(b"")
            runner._save_json(captures["terminal"], {"returncode": 1, "failed_step": None, "fault_code": None})
            runner._save_json(captures["metadata"], {"wrapper_pid": index + 1, "cli_pid": index + 3})
            reservation = {"schema_version": 1, "attempt_id": attempt, "slot_id": "canary:structured", "kind": "canary",
                           "schedule_index": None, "reserved_utc": runner.utc_now(), "context_sha256": context_sha256}
            custody = {"cleanup_proven": True, "forced_cleanup": False, "active_processes_final": 0,
                       "judge_directory_cleaned": True, "marker_echo": False, "tool_event": False}
            sidecar = {"attempt_id": attempt, "kind": "canary", "slot_id": "canary:structured",
                       "context_sha256": context_sha256, "status": status, "verdict": None, "reason": None,
                       "returncode": 1, "cli": {"configuration_sha256": "a" * 64}, "scientific_sha256": "b" * 64,
                       **custody}
            for name, path in captures.items():
                sidecar[f"{name}_path"] = str(path)
                sidecar[f"{name}_sha256"] = runner._file_digest(path)
                if name in {"stdout", "stderr"}:
                    sidecar[f"{name}_bytes"] = path.stat().st_size
            runner._save_json(self.private / "reservations" / f"{attempt}.json", reservation)
            runner._save_json(self.private / "sidecars" / f"{attempt}.json", sidecar)
            receipt = {"attempt_id": attempt, "context_sha256": context_sha256, "status": status,
                       "verdict": None, "reason": None, **custody}
            receipt["sidecar_sha256"] = runner._file_digest(self.private / "sidecars" / f"{attempt}.json")
            runner._save_json(self.private / "receipts" / f"{attempt}.json", receipt)
        history.ensure_history(self.private)


if __name__ == "__main__":
    unittest.main()
