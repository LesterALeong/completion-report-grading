from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from unittest.mock import patch

import screen


class FollowupScreenTests(unittest.TestCase):
    def test_checked_in_pairs_satisfy_the_frozen_eligibility_matrix(self):
        summary = screen.run_screen()
        self.assertEqual(summary["score"]["status"], "TARGET_MET")
        self.assertEqual(summary["score"]["eligible_pair_count"], 6)
        self.assertEqual(len(summary["cases"]), 6)
        self.assertEqual(len({case["family"] for case in summary["cases"]}), 4)
        for case in summary["cases"]:
            self.assertTrue(case["eligible"], case["failed_criteria"])
            self.assertTrue(case["criteria"]["both_variants_pass_visible_examples"])
            self.assertTrue(case["criteria"]["correct_variant_passes_contract_checks"])
            self.assertTrue(case["criteria"]["flawed_variant_mismatches_intentional_witness"])
            self.assertTrue(case["criteria"]["neither_variant_has_runtime_errors"])

    def test_inventory_rejects_missing_pair_and_wrong_fixture_count(self):
        inventory = screen.load_inventory()
        del inventory["cases"][-1]
        with self.assertRaisesRegex(ValueError, "exactly 6 cases"):
            screen.validate_inventory(inventory)

        inventory = screen.load_inventory()
        inventory["fixture_file_count"] = 11
        with self.assertRaisesRegex(ValueError, "frozen count"):
            screen.validate_inventory(inventory)

    def test_changed_witness_cannot_keep_pair_eligible(self):
        case = copy.deepcopy(screen.load_inventory()["cases"][0])
        witness = next(check for check in case["contract_checks"] if check["witness"])
        witness["expected"] = [["a", "b"], ["c", "d"]]
        result = screen._evaluate_case(case)
        self.assertFalse(result["eligible"])
        self.assertIn("correct_variant_passes_contract_checks", result["failed_criteria"])
        self.assertIn("flawed_variant_mismatches_intentional_witness", result["failed_criteria"])

    def test_identical_variants_do_not_supply_a_defect_witness(self):
        case = screen.load_inventory()["cases"][0]
        correct_source, correct_sha256 = screen._normalized_source(case["correct_path"])
        original_reader = screen._normalized_source

        def identical_source(path: str) -> tuple[str, str]:
            if path == case["flawed_path"]:
                return correct_source, correct_sha256
            return original_reader(path)

        with patch.object(screen, "_normalized_source", side_effect=identical_source):
            result = screen._evaluate_case(case)
        self.assertFalse(result["eligible"])
        self.assertEqual(
            result["variants"]["correct"]["source_sha256"],
            result["variants"]["flawed"]["source_sha256"],
        )
        self.assertFalse(result["criteria"]["flawed_variant_mismatches_intentional_witness"])

    def test_visible_failure_is_not_counted_as_a_flaw_witness(self):
        case = screen.load_inventory()["cases"][0]
        wrong_source = f"def {case['function_name']}({', '.join(case['parameters'])}):\n    return None\n"
        original_reader = screen._normalized_source

        def visible_failure(path: str) -> tuple[str, str]:
            if path == case["correct_path"]:
                return wrong_source, "1" * 64
            return original_reader(path)

        with patch.object(screen, "_normalized_source", side_effect=visible_failure):
            result = screen._evaluate_case(case)
        self.assertFalse(result["eligible"])
        self.assertIn("both_variants_pass_visible_examples", result["failed_criteria"])
        self.assertTrue(result["criteria"]["neither_variant_has_runtime_errors"])

    def test_actual_cli_replays_deterministically(self):
        output_path = screen.SCREEN_SUMMARY_PATH
        command = [
            sys.executable,
            "-S",
            "-B",
            str(screen.FOLLOWUP_DIR / "screen.py"),
            "--output",
            str(output_path),
        ]
        baseline_bytes = output_path.read_bytes()
        first = subprocess.run(command, cwd=screen.ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(first.returncode, 0, first.stderr)
        first_bytes = output_path.read_bytes()
        self.assertEqual(first_bytes, baseline_bytes)
        first_summary = json.loads(first_bytes)
        self.assertEqual(first_summary["score"]["status"], "TARGET_MET")

        second = subprocess.run(command, cwd=screen.ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(output_path.read_bytes(), first_bytes)
        self.assertIn("eligible_pairs=6/6", second.stdout)

    def test_actual_cli_refuses_a_protected_existing_destination(self):
        protected_path = screen.ROOT / "study" / "protocol.json"
        protected_bytes = protected_path.read_bytes()
        command = [
            sys.executable,
            "-S",
            "-B",
            str(screen.FOLLOWUP_DIR / "screen.py"),
            "--output",
            str(protected_path),
        ]
        result = subprocess.run(command, cwd=screen.ROOT, capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("canonical docs/followup/results/screen-summary.json", result.stderr)
        self.assertEqual(protected_path.read_bytes(), protected_bytes)


if __name__ == "__main__":
    unittest.main()
