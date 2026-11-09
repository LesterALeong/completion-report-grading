"""Model-free checks of documented command boundaries in a clean subprocess."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from study.data import ROOT
from study.protocol import TASK_TMP


class EntrypointTests(unittest.TestCase):
    def test_public_replay_refuses_missing_bundle_without_cli_or_private_state(self):
        TASK_TMP.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="public replay boundary ", dir=TASK_TMP) as temporary:
            task_root = Path(temporary)
            private_root = task_root / "private-must-stay-absent"
            environment = os.environ.copy()
            environment["PATH"] = ""
            environment["COMPLETION_REPORT_TMP"] = str(private_root)
            completed = subprocess.run(
                [sys.executable, "-m", "study", "analyze", "--split", "holdout",
                 "--bundle", str(task_root / "missing-public-bundle"),
                 "--scope", "public_projection_replay", "--manifest-sha256", "0" * 64],
                cwd=ROOT.parent, env=environment, text=True, capture_output=True,
                timeout=20, check=False,
            )
            self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
            # A rejected manifest must not turn into an auth/CLI discovery attempt.
            self.assertNotIn("codex executable was not found", completed.stderr)
            self.assertFalse(private_root.exists())

    def test_run_without_authorization_refuses_before_reading_a_freeze(self):
        completed = subprocess.run(
            [sys.executable, "-m", "study", "run", "--split", "holdout"],
            cwd=ROOT.parent, text=True, capture_output=True, timeout=20, check=False,
        )
        self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
        self.assertIn("authoriz", (completed.stdout + completed.stderr).lower())
        if completed.stdout.strip().startswith("{"):
            self.assertNotEqual(json.loads(completed.stdout).get("status"), "PASS")


if __name__ == "__main__":
    unittest.main()
