import os
import unittest
from unittest.mock import patch

from study.data import load_cases, load_protocol
from study.oracle_checks import evaluate_all, load_oracle
from study.prompt import build_prompt
from study.protocol import (
    TASK_TMP,
    check_report_pair,
    tokenizer_counter,
    validate_input_parity,
    validate_inventory,
)


class ProtocolTests(unittest.TestCase):
    def test_frozen_split_and_family_counts(self):
        summary = validate_inventory()
        self.assertEqual(summary["development_cases"], 8)
        self.assertEqual(summary["development_families"], 2)
        self.assertEqual(summary["holdout_cases"], 18)
        self.assertEqual(summary["holdout_families"], 3)
        self.assertEqual(summary["holdout_defective"], 12)
        self.assertEqual(summary["holdout_correct"], 6)
        self.assertEqual(summary["planned_study_cells"], 104)

    def test_oracle_covers_every_criterion_and_witnesses_each_defect(self):
        oracle = load_oracle()
        results = {item["case_id"]: item for item in evaluate_all()}
        for split in ("development", "holdout"):
            for case in load_cases(split):
                truth = oracle[case["case_id"]]
                result = results[case["case_id"]]
                self.assertEqual(set(result["criterion_coverage"]), {item["id"] for item in case["criteria"]})
                self.assertTrue(all(result["criterion_coverage"].values()))
                if truth["label"] == "defective":
                    self.assertTrue(any(item["witness"] and not item["passed"] for item in result["checks"]))
                else:
                    self.assertTrue(result["checks"])
                    self.assertTrue(all(item["passed"] for item in result["checks"]))

    def test_condition_payload_has_no_labels_or_sibling_markers(self):
        case = load_cases("holdout")[0]
        marker = "SIBLING-OUTPUT-SECRET-7462"
        for condition in load_protocol()["conditions"]:
            prompt = build_prompt(case, condition)
            self.assertNotIn(case["case_id"], prompt)
            self.assertNotIn("defective", prompt)
            self.assertNotIn("correct", prompt)
            self.assertNotIn("HOLD-F1", prompt)
            self.assertNotIn(marker, prompt)
            self.assertNotIn("oracle.json", prompt)
        parity = validate_input_parity()
        self.assertEqual(parity["cases_checked"], 26)

    def test_report_template_and_cached_tokenizer_parity(self):
        counter, cache = tokenizer_counter()
        result = check_report_pair(lambda text: len(counter(text)))
        self.assertEqual(result["token_status"], "PASS")
        self.assertEqual(result["tokenizer"]["version"], "0.13.0")
        self.assertEqual(result["tokenizer"]["encoding"], "o200k_base")
        self.assertTrue(cache["cache_present"])
        self.assertLessEqual(result["word_difference_fraction"], 0.05)
        self.assertLessEqual(result["token_difference_fraction"], 0.05)

    def test_missing_tokenizer_cache_blocks_without_network_fallback(self):
        missing_cache = TASK_TMP / "definitely-missing-token-cache"
        with patch.dict(os.environ, {"TIKTOKEN_CACHE_DIR": str(missing_cache)}):
            from study.protocol import TokenizerUnavailable

            with self.assertRaises(TokenizerUnavailable):
                tokenizer_counter()


if __name__ == "__main__":
    unittest.main()
