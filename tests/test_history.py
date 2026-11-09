import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from study import evidence, history, runner
from study.data import ROOT, load_protocol
from study.prompt import build_prompt
from study.protocol import TASK_TMP


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class HistoryTests(unittest.TestCase):
    def setUp(self):
        TASK_TMP.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="legacy-history-", dir=TASK_TMP)
        self.root = Path(self.temp.name)
        for name in ("reservations", "receipts", "sidecars", "captures"):
            (self.root / name).mkdir()
        for index, attempt in enumerate(history.ATTEMPT_IDS):
            capture = self.root / "captures" / attempt
            capture.mkdir()
            paths = {name: capture / f"{name}.bin" for name in ("stdout", "stderr", "terminal", "metadata")}
            paths["stdout"].write_bytes(b"synthetic output")
            paths["stderr"].write_bytes(b"synthetic diagnostics")
            paths["terminal"].write_text(json.dumps({"returncode": 0, "failed_step": None, "fault_code": None}), encoding="utf-8")
            paths["metadata"].write_text(json.dumps({"wrapper_pid": 1, "cli_pid": 2}), encoding="utf-8")
            context = str(index + 1) * 64
            status = "protocol_invalid" if index == 0 else "operational_unknown"
            reservation = {"attempt_id": attempt, "kind": "canary", "slot_id": "canary:structured", "context_sha256": context}
            sidecar = {**reservation, "status": status, "reason": None, "verdict": None, "returncode": 0,
                       "cleanup_proven": True, "forced_cleanup": False, "active_processes_final": 0,
                       "judge_directory_cleaned": True, "marker_echo": False, "tool_event": bool(index == 0),
                       "scientific_sha256": "a" * 64, "cli": {"configuration_sha256": "b" * 64}}
            for name, path in paths.items():
                sidecar[f"{name}_path"] = str(path)
                sidecar[f"{name}_sha256"] = digest(path)
                if name in {"stdout", "stderr"}:
                    sidecar[f"{name}_bytes"] = path.stat().st_size
            reservation_path = self.root / "reservations" / f"{attempt}.json"
            sidecar_path = self.root / "sidecars" / f"{attempt}.json"
            reservation_path.write_text(json.dumps(reservation), encoding="utf-8")
            sidecar_path.write_text(json.dumps(sidecar), encoding="utf-8")
            receipt = {"attempt_id": attempt, "context_sha256": context, "status": status, "reason": None, "verdict": None,
                       "sidecar_sha256": digest(sidecar_path), **{key: sidecar[key] for key in (
                           "cleanup_proven", "forced_cleanup", "active_processes_final", "judge_directory_cleaned", "marker_echo", "tool_event")}}
            (self.root / "receipts" / f"{attempt}.json").write_text(json.dumps(receipt), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_manifest_is_create_only_and_reopens_all_original_bytes(self):
        result = history.ensure_history(self.root)
        self.assertEqual([row["attempt_id"] for row in result["manifest"]["attempts"]], list(history.ATTEMPT_IDS))
        self.assertTrue(all(row["admitted"] is False for row in result["manifest"]["attempts"]))
        self.assertEqual(history.verify_history(self.root), result)
        self.assertEqual(history.ensure_history(self.root), result)
        (self.root / "captures" / history.ATTEMPT_IDS[0] / "stdout.bin").write_bytes(b"tampered")
        with self.assertRaises(evidence.EvidenceError):
            history.verify_history(self.root)

    def test_missing_and_unexpected_history_block(self):
        history.ensure_history(self.root)
        path = self.root / history.MANIFEST_NAME
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["attempts"].append(dict(manifest["attempts"][0]))
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(evidence.EvidenceError):
            history.verify_history(self.root)
        path.unlink()
        (self.root / "receipts" / f"{history.ATTEMPT_IDS[0]}.json").unlink()
        with self.assertRaises(evidence.EvidenceError):
            history.ensure_history(self.root)

    def test_capture_path_outside_root_blocks(self):
        attempt = history.ATTEMPT_IDS[0]
        path = self.root / "sidecars" / f"{attempt}.json"
        sidecar = json.loads(path.read_text(encoding="utf-8"))
        sidecar["stdout_path"] = str(self.root.parent / "outside.bin")
        path.write_text(json.dumps(sidecar), encoding="utf-8")
        receipt_path = self.root / "receipts" / f"{attempt}.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["sidecar_sha256"] = digest(path)
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        with self.assertRaises(evidence.EvidenceError):
            history.ensure_history(self.root)

    def test_protocol_preserves_scientific_fields_and_schedule(self):
        old = json.loads((ROOT.parent / "docs" / "protocols" / "codex-v1.json").read_text(encoding="utf-8"))
        new = load_protocol()
        excluded = {"study_id", "model", "cli"}
        self.assertEqual({k: v for k, v in old.items() if k not in excluded},
                         {k: v for k, v in new.items() if k not in {"schema_version", "provider", "study_id", "model", "transport", "history"}})
        self.assertEqual(new["schema_version"], 2)
        self.assertEqual(new["provider"], "ollama_local")
        self.assertEqual(new["history"]["attempt_ids"], list(history.ATTEMPT_IDS))
        with patch.object(runner, "load_protocol", return_value=old):
            before = runner.ordered_schedule()
        with patch.object(runner, "load_protocol", return_value=new):
            after = runner.ordered_schedule()
        self.assertEqual(before, after)
        self.assertEqual(len(after), 104)
        for cell in after:
            case = next(item for item in runner.load_cases(cell["split"]) if item["case_id"] == cell["case_id"])
            self.assertEqual(hashlib.sha256(build_prompt(case, cell["condition"]).encode()).hexdigest(), cell["prompt_sha256"])

    def test_preserved_science_bytes_match_archived_v1(self):
        fixture = Path(__file__).parent / "fixtures" / "science-v1.sha256.json"
        golden = json.loads(fixture.read_text(encoding="utf-8"))
        self.assertEqual(golden["archive_sha256"], "dcc0597fab9eefb1f89657f0a16ad2e888fd5e02dae159bbafa8520bb5709614")
        expected_names = {"study/cases/development.json", "study/cases/holdout.json", "study/data.py", "study/prompt.py",
                          "study/reports.py", "study/oracle.json", "study/oracle_checks.py", "study/output.schema.json",
                          "study/prompts/common.md", "study/prompts/mitigation.md"}
        self.assertEqual(set(golden["files"]), expected_names)
        for name, expected in golden["files"].items():
            with self.subTest(path=name):
                self.assertEqual(digest(ROOT.parent / name), expected)
        archive = TASK_TMP / "candidates" / "codex-v1-closed.zip"
        if archive.is_file():
            self.assertEqual(digest(archive), golden["archive_sha256"])
            with zipfile.ZipFile(archive) as saved:
                for name in expected_names:
                    with self.subTest(path=name):
                        self.assertEqual(hashlib.sha256(saved.read(name)).hexdigest(), golden["files"][name])

    def test_science_golden_without_private_archive(self):
        with patch(f"{__name__}.TASK_TMP", self.root):
            self.test_preserved_science_bytes_match_archived_v1()


if __name__ == "__main__":
    unittest.main()
