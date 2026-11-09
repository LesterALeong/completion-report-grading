import json
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from study import analysis, evidence
from study.analysis import (
    PRIVATE_SCOPE,
    PUBLIC_SCOPE,
    BlockedDiagnostic,
    _analyze_receipts,
    analyze,
    framing_screen,
    load_verified_bundle,
    paired_contrast,
    reconcile,
    wilson_interval,
)
from study.data import load_cases, load_protocol
from study.prompt import COMMON_PROMPT, build_prompt


_READ_JSON = evidence.read_json


def _read_manifest_v1_elsewhere(path):
    if Path(path).name == "manifest.json":
        return {"schema_version": 1}
    return _READ_JSON(path)


# Synthetic stats-only fixture; these receipts never enter the evidence loader.
def valid_receipt(split, case, condition, verdict="PASS"):
    prompt = build_prompt(case, condition)
    input_hashes = {
        "code": analysis._sha256(case["code"].encode("utf-8")),
        "task": analysis._sha256(case["task"].encode("utf-8")),
        "criteria": analysis._sha256(analysis._canonical_json(case["criteria"])),
        "common_prompt": analysis._sha256(COMMON_PROMPT.encode("utf-8")),
        "prompt": analysis._sha256(prompt.encode("utf-8")),
    }
    return {
        "slot_id": f"study:{split}:{case['case_id']}:{condition}",
        "kind": "study",
        "status": "valid",
        "verdict": verdict,
        "reason": "checked against stated criterion",
        "timestamp_utc": "2026-11-09T12:00:00Z",
        "requested_model": analysis._legacy_protocol()["model"]["requested_alias"],
        "reasoning_effort": analysis._legacy_protocol()["model"]["reasoning_effort"],
        "scientific_sha256": "c" * 64,
        "cli": {
            "version": "0.166.0-alpha.5.1",
            "binary_sha256": "a" * 64,
            "configuration_sha256": "b" * 64,
            "version_check_passed": True,
        },
        "input_sha256": input_hashes,
        "terminal_exit": 0,
        "timed_out": False,
        "cleanup_proven": True,
        "forced_cleanup": False,
        "active_processes_final": 0,
        "judge_directory_cleaned": True,
    }


# Synthetic verifier return value; tests patch the evidence verifier around it.
def _empty_current_public_bundle():
    protocol = analysis._legacy_protocol()
    scientific_files = evidence.scientific_closure(analysis.REPO_ROOT)
    schedule = analysis._ordered_schedule()
    cli = {
        "version": "synthetic-cli-version",
        "binary_sha256": "a" * 64,
        "configuration_sha256": "b" * 64,
        "version_check_passed": True,
    }
    freeze = {
        "schema_version": 1,
        "scientific_files": scientific_files,
        "scientific_sha256": evidence.freeze_sha256(scientific_files),
        "protocol": protocol,
        "schedule": schedule,
        "cli": cli,
        "auth_route": "chatgpt_subscription",
        "admission": {
            "status": "PASS",
            "scientific_sha256": evidence.freeze_sha256(scientific_files),
            "cli": cli,
        },
        "frozen_utc": "2026-11-09T12:00:00Z",
    }
    freeze_sha256 = evidence.freeze_sha256(freeze)
    return {
        "verification_scope": PUBLIC_SCOPE,
        "freeze_sha256": freeze_sha256,
        "freeze": freeze,
        "reservations": [],
        "admission_context": {},
        "receipts": [],
        "canary_ledger": [],
        "canary_reservations": 0,
        "history": None,
    }


def _valid_event_stream():
    events = [
        {"type": "thread.started", "thread_id": "private-thread-id"},
        {"type": "turn.started"},
        {"type": "item.started", "item": {"type": "reasoning"}},
        {"type": "item.completed", "item": {"type": "reasoning"}},
        {"type": "item.completed", "item": {
            "type": "agent_message",
            "text": '{"verdict":"PASS","reason":"criterion met"}',
        }},
        {"type": "turn.completed", "model": "gpt-6-luna"},
    ]
    return "\n".join(analysis._canonical_json(event).decode("utf-8") for event in events) + "\n"


class AnalysisTests(unittest.TestCase):
    def test_wilson_bounds_are_finite_for_zero_and_full_rates(self):
        self.assertEqual(wilson_interval(0, 0), [0.0, 1.0])
        zero_rate = wilson_interval(0, 10)
        full_rate = wilson_interval(10, 10)
        self.assertAlmostEqual(zero_rate[0], 0.0)
        self.assertAlmostEqual(zero_rate[1], 0.2775328, places=6)
        self.assertAlmostEqual(full_rate[0], 0.7224672, places=6)
        self.assertAlmostEqual(full_rate[1], 1.0)

    def test_paired_bootstrap_golden_counts_and_missingness_threshold(self):
        cells = []
        observations = {
            "D01": ("DEV-F1", 1, 0),
            "D02": ("DEV-F1", 0, 0),
            "D05": ("DEV-F2", 1, 0),
            "D06": ("DEV-F2", None, 0),
        }
        for case_id, (family, persuasive, neutral) in observations.items():
            for condition, outcome in (("persuasive", persuasive), ("neutral", neutral)):
                valid = outcome is not None
                cells.append({
                    "case_id": case_id,
                    "family": family,
                    "label": "defective",
                    "condition": condition,
                    "status": "valid" if valid else "invalid_output",
                    "verdict": ("PASS" if outcome else "FAIL") if valid else None,
                })
        contrast = paired_contrast(cells, "defective", "persuasive", "neutral", "false_pass", 4, 10000, 20261109)
        self.assertEqual(contrast["complete_valid_pairs"], 3)
        self.assertEqual(contrast["raw_difference_count"], 2)
        self.assertAlmostEqual(contrast["risk_difference"], 2 / 3)
        self.assertEqual(contrast["discordant_left_only"], 2)
        self.assertEqual(contrast["discordant_right_only"], 0)
        self.assertEqual(contrast["concordant"], 1)
        self.assertEqual(contrast["family_pair_counts"], {"DEV-F1": 2, "DEV-F2": 1})
        self.assertEqual(contrast["missingness_bounds_count"], [1, 3])
        self.assertEqual(contrast["paired_bootstrap_95"], paired_contrast(
            cells, "defective", "persuasive", "neutral", "false_pass", 4, 10000, 20261109
        )["paired_bootstrap_95"])
        self.assertEqual(framing_screen(contrast, 2)["status"], "inconclusive_missingness_can_reverse")

    def test_reducer_accounts_for_missing_and_failure_categories(self):
        cases = load_cases("holdout")
        conditions = load_protocol()["conditions"]
        receipts = []
        dispositions = ["valid", "protocol_invalid", "invalid_output", "operational_unknown"]
        first = cases[0]["case_id"]
        for index, condition in enumerate(conditions):
            status = dispositions[index]
            if status == "valid":
                receipts.append(valid_receipt("holdout", cases[0], condition))
            else:
                receipts.append({
                    "call_type": "study",
                    "slot_id": f"study:holdout:{first}:{condition}",
                    "status": status,
                    "verdict": None,
                })
        result = _analyze_receipts("holdout", receipts)
        self.assertEqual(result["planned_cells"], 72)
        self.assertEqual(result["accounted_cells"], 72)
        counts = result["condition_tables"]
        self.assertEqual(counts["report_free"]["status_counts"]["valid"], 1)
        self.assertEqual(counts["neutral"]["status_counts"]["protocol_invalid"], 1)
        self.assertEqual(counts["persuasive"]["status_counts"]["invalid_output"], 1)
        self.assertEqual(counts["mitigation"]["status_counts"]["operational_unknown"], 18)
        self.assertEqual(counts["report_free"]["false_passes_on_defects"]["planned_denominator"], 12)
        self.assertEqual(counts["report_free"]["false_passes_on_defects"]["valid_denominator"], 1)
        self.assertEqual(counts["report_free"]["correct_nonpasses"]["wilson_95"], [0.0, 1.0])

    def test_duplicate_cells_become_protocol_invalid(self):
        case = load_cases("development")[0]
        case_id = case["case_id"]
        receipt = valid_receipt("development", case, "report_free")
        result = reconcile("development", [receipt, receipt])
        cell = next(item for item in result["cells"] if item["case_id"] == case_id and item["condition"] == "report_free")
        self.assertEqual(cell["status"], "protocol_invalid")
        self.assertIsNone(cell["verdict"])

    def test_tampered_input_hash_is_protocol_invalid(self):
        case = load_cases("development")[0]
        receipt = valid_receipt("development", case, "report_free")
        receipt["input_sha256"]["prompt"] = "0" * 64
        result = reconcile("development", [receipt])
        cell = next(item for item in result["cells"] if item["case_id"] == case["case_id"] and item["condition"] == "report_free")
        self.assertEqual(cell["status"], "protocol_invalid")
        self.assertIsNone(cell["verdict"])

    def test_v2_reconciliation_uses_nested_runtime_identity_without_cli_fields(self):
        case = load_cases("development")[0]
        receipt = valid_receipt("development", case, "report_free")
        protocol = load_protocol()
        model = protocol["model"]["requested_alias"]
        receipt.update({
            "schema_version": 2,
            "provider": "ollama_local",
            "reported_model": model,
            "marker_echo": False,
            "transport": {
                "configuration_sha256": "b" * 64,
                "runtime_identity_sha256": "c" * 64,
                "runtime_identity": {"observed": {"model": model}},
            },
        })
        receipt.pop("requested_model")
        receipt.pop("reasoning_effort")
        receipt.pop("cli")

        result = reconcile("development", [receipt])
        cell = next(item for item in result["cells"] if item["case_id"] == case["case_id"] and item["condition"] == "report_free")
        self.assertEqual((cell["status"], cell["verdict"]), ("valid", "PASS"))
        self.assertNotIn("event_count", receipt)

        receipt["transport"]["runtime_identity"]["observed"]["model"] = "another-model"
        result = reconcile("development", [receipt])
        cell = next(item for item in result["cells"] if item["case_id"] == case["case_id"] and item["condition"] == "report_free")
        self.assertEqual(cell["status"], "protocol_invalid")

    def test_analyze_blocks_unverified_receipt_inputs_without_tables(self):
        for unverified in ([], {}, [{"status": "valid", "verdict": "PASS"}]):
            with self.subTest(input_type=type(unverified).__name__):
                result = analyze("holdout", unverified)
                self.assertEqual(result, {"status": "BLOCKED", "diagnostic": "UNVERIFIED_INPUT"})
                self.assertNotIn("condition_tables", result)
                self.assertNotIn("cells", result)

    def test_public_verified_prefix_keeps_unattempted_suffix_in_missingness(self):
        verified_public = _empty_current_public_bundle()
        with patch("study.analysis.evidence.read_json", side_effect=_read_manifest_v1_elsewhere):
            with patch("study.analysis.evidence.verify_public_bundle", return_value=verified_public):
                bundle = load_verified_bundle(Path("unused-public-bundle"), scope=PUBLIC_SCOPE, manifest_sha256="d" * 64)

        self.assertNotIsInstance(bundle, BlockedDiagnostic)
        self.assertEqual(bundle.verification_scope, PUBLIC_SCOPE)
        result = analyze("holdout", bundle)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["verification_scope"], PUBLIC_SCOPE)
        self.assertEqual(result["planned_cells"], 72)
        self.assertEqual(result["accounted_cells"], 72)
        self.assertEqual(result["valid_cells"], 0)
        self.assertEqual(result["condition_tables"]["report_free"]["status_counts"]["operational_unknown"], 18)

    def test_public_loader_replays_projection_without_cli_auth_or_native_calls(self):
        verified_public = _empty_current_public_bundle()

        def verify(_root, _manifest_sha256, replay):
            parsed = replay(_valid_event_stream(), 0, False)
            self.assertEqual((parsed.status, parsed.verdict), ("valid", "PASS"))
            return verified_public

        with patch("study.analysis.evidence.read_json", side_effect=_read_manifest_v1_elsewhere):
            with patch("study.analysis.evidence.verify_public_bundle", side_effect=verify):
                with patch("study.codex_cli.inspect_cli") as inspect_cli:
                    with patch("study.codex_cli.chatgpt_login_status") as login_status:
                        with patch("study.codex_cli.run_codex") as run_codex:
                            with patch("study.windows_job.run_native") as run_native:
                                bundle = load_verified_bundle(Path("unused-public-bundle"), scope=PUBLIC_SCOPE, manifest_sha256="d" * 64)

        self.assertNotIsInstance(bundle, BlockedDiagnostic)
        inspect_cli.assert_not_called()
        login_status.assert_not_called()
        run_codex.assert_not_called()
        run_native.assert_not_called()

    def test_public_source_protocol_and_schedule_mismatches_block(self):
        base = _empty_current_public_bundle()
        cases = []

        stale_source = json.loads(json.dumps(base))
        stale_source["freeze"]["scientific_files"]["study/protocol.json"] = "0" * 64
        cases.append(("scientific", stale_source))

        wrong_protocol = json.loads(json.dumps(base))
        wrong_protocol["freeze"]["protocol"]["turn_budget"]["study"] += 1
        cases.append(("protocol", wrong_protocol))

        wrong_schedule = json.loads(json.dumps(base))
        wrong_schedule["freeze"]["schedule"].reverse()
        cases.append(("schedule", wrong_schedule))

        for name, payload in cases:
            with self.subTest(mismatch=name):
                with patch("study.analysis.evidence.read_json", side_effect=_read_manifest_v1_elsewhere):
                    with patch("study.analysis.evidence.verify_public_bundle", return_value=payload):
                        result = load_verified_bundle(Path("unused-public-bundle"), scope=PUBLIC_SCOPE, manifest_sha256="d" * 64)
                self.assertIsInstance(result, BlockedDiagnostic)
                self.assertIn(result.code, {"SCIENTIFIC_FILES", "PROTOCOL_MISMATCH", "SCHEDULE_MISMATCH", "FREEZE_DIGEST"})

    def test_private_missing_raw_bundle_blocks_without_public_fallback(self):
        fake_runner = types.ModuleType("study.runner")
        fake_runner.load_private_bundle = lambda _root: (_ for _ in ()).throw(evidence.EvidenceError("RAW_CAPTURE_UNREADABLE"))
        with patch.dict("sys.modules", {"study.runner": fake_runner}):
            with patch("study.analysis.evidence.verify_public_bundle") as verify_public:
                result = load_verified_bundle(Path("unused-private-root"), scope=PRIVATE_SCOPE)

        self.assertEqual(result, BlockedDiagnostic("RAW_CAPTURE_UNREADABLE"))
        verify_public.assert_not_called()

    def test_verified_bundle_nested_values_are_returned_as_copies(self):
        verified_public = _empty_current_public_bundle()
        with patch("study.analysis.evidence.read_json", side_effect=_read_manifest_v1_elsewhere):
            with patch("study.analysis.evidence.verify_public_bundle", return_value=verified_public):
                bundle = load_verified_bundle(Path("unused-public-bundle"), scope=PUBLIC_SCOPE, manifest_sha256="d" * 64)

        first_freeze = bundle.freeze
        first_freeze["protocol"]["conditions"].clear()
        self.assertEqual(bundle.freeze["protocol"]["conditions"], load_protocol()["conditions"])
        first_receipts = bundle.receipts
        first_receipts.append({"status": "valid"})
        self.assertEqual(bundle.receipts, [])


if __name__ == "__main__":
    unittest.main()
