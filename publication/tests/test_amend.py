import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from publication import amend
from study import evidence, ollama
from study.protocol import canonical_json


MODEL = "qwen3.5:9b-q4_K_M"


def projection(reason):
    return canonical_json({"schema_version": 1, "provider": "ollama_local", "facts": {
        "transport_checks": {name: True for name in ollama.TRANSPORT_CHECKS}, "envelope_clean": True,
        "model": MODEL, "tool_violation": False, "thinking_violation": False, "content_valid": True,
        "verdict": "FAIL", "reason": evidence._public_reason(reason)}})


def receipt(reason):
    return {"status": "valid", "verdict": "FAIL", "reason": reason, "reported_model": MODEL}


class AmendmentTests(unittest.TestCase):
    def test_all_redaction_classes_and_unicode_boundary(self):
        for fragment in ("a/b", "C:\\x", "/a/b", "a@b.co"):
            for size in (299, 300):
                with self.subTest(fragment=fragment, size=size):
                    reason = "é" * (size - len(fragment) - 1) + " " + fragment
                    redacted = evidence._public_reason(reason)
                    self.assertGreater(len(redacted), 300, fragment)
                    original = projection(reason)
                    self.assertEqual(ollama.parse_projection(original, MODEL).status, "operational_unknown")
                    fixed, bounded = amend.amended_projection(original, receipt(reason), MODEL)
                    self.assertEqual(bounded, redacted[:299] + "…")
                    self.assertEqual(len(bounded), 300)
                    self.assertEqual(evidence._public_reason(bounded), bounded)
                    parsed = ollama.parse_projection(fixed, MODEL)
                    self.assertEqual((parsed.status, parsed.verdict, parsed.reported_model), ("valid", "FAIL", MODEL))
        reason = ("é " * 138) + "x" * 24
        redacted = evidence._public_reason(reason)
        self.assertLessEqual(len(redacted), 300)
        self.assertEqual(evidence._public_reason(redacted), redacted)
        with self.assertRaisesRegex(ValueError, "NOT_OVERFLOW"):
            amend.amended_projection(projection(reason), receipt(reason), MODEL)

    def test_nonoverflow_and_malformed_refuse(self):
        for length in (299, 300):
            reason = "a " * (length // 2) + ("a" if length % 2 else "")
            with self.assertRaisesRegex(ValueError, "NOT_OVERFLOW"):
                amend.amended_projection(projection(reason), receipt(reason), MODEL)
        with self.assertRaises((ValueError, evidence.EvidenceError)):
            amend.amended_projection(b"{", receipt("bad"), MODEL)
        with tempfile.TemporaryDirectory(prefix="inert-manifest-", dir=Path(__file__).parent) as temporary:
            root = Path(temporary)
            (root / "manifest.json").write_bytes(b"{}")
            with self.assertRaisesRegex(ValueError, "ORIGINAL_MANIFEST"):
                amend._read_original(root, "0" * 64)

    def test_grade_or_model_change_refuses(self):
        reason = ("é " * 150)[:297] + "a/b"
        original = projection(reason)
        changed = copy.deepcopy(receipt(reason))
        changed["verdict"] = "PASS"
        with self.assertRaisesRegex(ValueError, "CLASSIFICATION_CHANGED"):
            amend.amended_projection(original, changed, MODEL)
        changed = copy.deepcopy(receipt(reason))
        changed["reported_model"] = "other"
        with self.assertRaisesRegex(ValueError, "CLASSIFICATION_CHANGED"):
            amend.amended_projection(original, changed, MODEL)

    def test_retained_actual_projection_red_to_green(self):
        fixtures = Path(__file__).parent / "fixtures"
        raw = (fixtures / "retained_projection.json").read_bytes().removesuffix(b"\n").removesuffix(b"\r")
        source = evidence.read_json(fixtures / "retained_receipt.json")
        self.assertEqual(hashlib.sha256(raw).hexdigest(), "771e5b1606a9970ea7855c70848bfa0779666abbdf05a6942a5d91d3fb8917c0")
        self.assertEqual(hashlib.sha256(source["reason"].encode("utf-8")).hexdigest(), "e6b369c5547ad08ba41707cd26b656e01148124b0ea5a22c898190d00d688ab6")
        self.assertEqual(len(source["reason"]), 300)
        self.assertEqual(len(evidence._json(raw)["facts"]["reason"]), 305)
        self.assertEqual(ollama.parse_projection(raw, MODEL).status, "operational_unknown")
        fixed, bounded = amend.amended_projection(raw, source, MODEL)
        parsed = ollama.parse_projection(fixed, MODEL)
        self.assertEqual((parsed.status, parsed.verdict, parsed.reported_model, parsed.reason),
                         (source["status"], source["verdict"], source["reported_model"], bounded))


if __name__ == "__main__":
    unittest.main()
