import json
import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

from study import codex_cli, evidence
from study.protocol import TASK_TMP
from study.windows_job import NativeResult


def event_stream(final_text, model="gpt-6-luna"):
    events = [
        {"type": "thread.started", "thread_id": "private-id-not-retained"},
        {"type": "turn.started"},
        {"type": "item.started", "item": {"type": "reasoning"}},
        {"type": "item.completed", "item": {"type": "reasoning"}},
        {"type": "item.completed", "item": {"type": "agent_message", "text": final_text}},
        {"type": "turn.completed", "model": model, "thread_id": "private-id-not-retained"},
    ]
    return "\n".join(json.dumps(event) for event in events) + "\n"


class CodexCliTests(unittest.TestCase):
    def setUp(self):
        archive = Path(__file__).resolve().parents[1] / "docs" / "protocols" / "codex-v1.json"
        protocol = json.loads(archive.read_text(encoding="utf-8"))
        legacy_protocol = patch.object(codex_cli, "load_protocol", return_value=protocol)
        legacy_protocol.start()
        self.addCleanup(legacy_protocol.stop)

    def test_argv_is_shell_free_compatible_with_paths_containing_spaces(self):
        executable = r"C:\Program Files\Codex CLI\codex.exe"
        schema = r"C:\Users\example\A Repo\output schema.json"
        argv = codex_cli.build_argv(executable, schema)
        self.assertEqual(argv[0], executable)
        self.assertEqual(argv[argv.index("--output-schema") + 1], str(Path(schema).resolve()))
        self.assertIn("--skip-git-repo-check", argv)
        self.assertIn("--ignore-user-config", argv)
        self.assertNotIn("--ignore-rules", argv)
        self.assertIn('web_search="disabled"', argv)
        self.assertIn("features.code_mode.enabled=false", argv)
        self.assertNotIn("code_mode", [argv[index + 1] for index, value in enumerate(argv[:-1]) if value == "--disable"])
        self.assertIn("code_mode_host", [argv[index + 1] for index, value in enumerate(argv[:-1]) if value == "--disable"])
        self.assertIn("--ephemeral", argv)
        self.assertIn("--json", argv)
        self.assertEqual(argv[argv.index("--sandbox") + 1], "read-only")
        for feature in ("shell_tool", "apps", "browser_use", "memories", "multi_agent", "hooks", "goals", "sleep_tool", "view_image", "image_generation"):
            self.assertIn(feature, argv)
            self.assertIn("--disable", argv)

    def test_child_environment_removes_api_route_overrides_but_keeps_codex_home(self):
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": "do-not-copy-this",
            "OPENAI_BASE_URL": "https://example.invalid",
            "CODEX_ACCESS_TOKEN": "do-not-copy-this-either",
            "CODEX_HOME": str(TASK_TMP / "codex-home"),
        }):
            environment = codex_cli.child_environment()
        self.assertNotIn("OPENAI_API_KEY", environment)
        self.assertNotIn("OPENAI_BASE_URL", environment)
        self.assertNotIn("CODEX_ACCESS_TOKEN", environment)
        self.assertIn("CODEX_HOME", environment)

    def test_login_status_accepts_only_chatgpt_route_on_zero_exit(self):
        cases = (
            (0, "", "Logged in using ChatGPT", True),
            (0, "Logged in using an API key", "", False),
            (0, "", "", False),
            (1, "", "Logged in using ChatGPT", False),
        )
        with patch.object(codex_cli, "find_executable", return_value="codex.exe"):
            for returncode, stdout, stderr, expected in cases:
                completed = CompletedProcess([], returncode, stdout, stderr)
                with self.subTest(returncode=returncode, stdout=bool(stdout), stderr=bool(stderr)):
                    with patch.object(codex_cli.subprocess, "run", return_value=completed):
                        self.assertEqual(codex_cli.chatgpt_login_status(), expected)

    def test_parses_realistic_structured_final_event_without_account_or_thread_ids(self):
        stream = event_stream('{"verdict":"PASS","reason":"criterion met"}')
        result = codex_cli.parse_event_stream(stream, 0)
        self.assertEqual(result.status, "valid")
        self.assertEqual(result.verdict, "PASS")
        self.assertEqual(result.reason, "criterion met")
        self.assertEqual(result.reported_model, "gpt-6-luna")
        self.assertEqual(result.event_count, 6)

    def test_error_item_always_refuses_grade_without_claiming_a_tool(self):
        events = [json.loads(line) for line in event_stream('{"verdict":"PASS","reason":"ok"}').splitlines()]
        error = {"type": "item.completed", "item": {"id": "item-error", "type": "error", "message": "private startup fault"}}
        for index in range(len(events) + 1):
            raw = "\n".join(json.dumps(event) for event in (events[:index] + [error] + events[index:]))
            with self.subTest(position=index):
                result = codex_cli.parse_event_stream(raw, 0)
                self.assertEqual((result.status, result.verdict, result.tool_event), ("operational_unknown", None, False))
                projection = evidence.project_stdout(raw.encode())
                self.assertNotIn(b"private startup fault", projection)
                replay = codex_cli.parse_event_stream(projection.decode(), 0)
                self.assertEqual((replay.status, replay.verdict, replay.tool_event), ("operational_unknown", None, False))
                self.assertEqual(codex_cli.parse_event_stream(raw, None, timed_out=True).status, "operational_unknown")

    def test_retained_producer_error_projection_has_bound_provenance(self):
        fixtures = Path(__file__).parent / "fixtures"
        projection = (fixtures / "structured_canary_startup_error.jsonl").read_bytes()
        provenance = json.loads((fixtures / "structured_canary_startup_error.provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(provenance["raw_sha256"], "71e1829d3c56918c98b150d0d6ea03588aeacedbc4fe212c53f19f330500d60b")
        self.assertEqual((len(projection), hashlib.sha256(projection).hexdigest()),
                         (provenance["projection_bytes"], provenance["projection_sha256"]))
        result = codex_cli.parse_event_stream(projection.decode("utf-8"), 0)
        self.assertEqual((result.status, result.verdict, result.tool_event), ("operational_unknown", None, False))
        sidecar = TASK_TMP / "sidecars" / f"{provenance['attempt_id']}.json"
        if sidecar.is_file():
            original = Path(json.loads(sidecar.read_text(encoding="utf-8"))["stdout_path"]).read_bytes()
            self.assertEqual((len(original), hashlib.sha256(original).hexdigest()), (provenance["raw_bytes"], provenance["raw_sha256"]))
            self.assertEqual(evidence.project_stdout(original), projection)

    def test_error_item_precedes_protocol_flags_at_native_caller(self):
        TASK_TMP.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="item-error-", dir=TASK_TMP) as temporary:
            base = Path(temporary)
            cwd = base / "judge"
            cwd.mkdir()
            fixture = (Path(__file__).parent / "fixtures" / "structured_canary_startup_error.jsonl").read_bytes()
            lines = fixture.splitlines(keepends=True)
            raw = b"".join(lines[:-1]) + b'{"type":"item.completed","item":{"type":"command_execution"}}\n' + lines[-1]
            def fake_native(argv, prompt, working_directory, capture_dir, timeout, env):
                stdout, stderr = capture_dir / "stdout.bin", capture_dir / "stderr.bin"
                stdout.write_bytes(raw)
                stderr.write_bytes(b"")
                return NativeResult(0, False, True, False, 0, None, "terminal_read", None,
                                    stdout, stderr, capture_dir / "terminal.json", capture_dir / "process.json")
            with patch.object(codex_cli, "TASK_TMP", base), patch.object(codex_cli, "find_executable", return_value="codex"), \
                    patch.object(codex_cli, "run_native", side_effect=fake_native):
                result = codex_cli.run_codex("prompt", cwd, 30)
            self.assertEqual((result.status, result.verdict), ("operational_unknown", None))
            self.assertTrue(result.tool_event)
            self.assertIn("forbidden_item", result.protocol_violations)

    def test_tool_unknown_and_malformed_events_are_protocol_invalid(self):
        tool = json.dumps({"type": "item.started", "item": {"type": "command_execution"}})
        unknown = json.dumps({"type": "new.event"})
        self.assertEqual(codex_cli.parse_event_stream(tool, 0).status, "protocol_invalid")
        self.assertEqual(codex_cli.parse_event_stream(unknown, 0).status, "protocol_invalid")
        self.assertEqual(codex_cli.parse_event_stream("{not-json}\n", 0).status, "protocol_invalid")

    def test_output_schema_and_process_failure_states_are_separate(self):
        for final in (
            "not json",
            '{"verdict":"MAYBE","reason":"x"}',
            '{"verdict":"PASS"}',
            '{"verdict":"PASS","reason":""}',
            '{"verdict":"PASS","reason":"x","extra":1}',
        ):
            self.assertEqual(codex_cli.parse_event_stream(event_stream(final), 0).status, "invalid_output")
        valid = event_stream('{"verdict":"PASS","reason":"criterion met"}')
        self.assertEqual(codex_cli.parse_event_stream(valid, 1).status, "operational_unknown")
        self.assertEqual(codex_cli.parse_event_stream(valid, None, timed_out=True).status, "operational_unknown")
        self.assertEqual(codex_cli.parse_event_stream('{"type":"turn.started"}', 0).status, "protocol_invalid")
        failure = json.dumps({"type": "turn.failed"})
        self.assertEqual(codex_cli.parse_event_stream(failure, 0).status, "operational_unknown")

    def test_lifecycle_rejects_topology_and_identity_contradictions(self):
        good = [json.loads(line) for line in event_stream('{"verdict":"PASS","reason":"ok"}').splitlines()]
        cases = [
            [good[4]],
            [good[0], good[0], *good[1:]],
            [good[1], good[0], *good[2:]],
            [good[0], good[1], good[5], good[4]],
            [*good[:5], good[4], good[5]],
            [*good, good[0]],
            [good[0], good[1], {"type": "item.started", "item": {"type": "command_execution"}}, *good[4:]],
            [good[0], good[1], {"type": "item.completed", "item": {"id": "x", "type": "reasoning"}},
             {"type": "item.completed", "item": {"id": "x", "type": "reasoning"}}, *good[4:]],
            [*good[:5], {"type": "turn.completed", "model": "one", "model_id": "two"}],
            [*good[:5], {"type": "turn.completed", "unrecognized": True}],
        ]
        for events in cases:
            with self.subTest(events=events):
                parsed = codex_cli.parse_event_stream("\n".join(map(json.dumps, events)), 0)
                self.assertEqual(parsed.status, "protocol_invalid")
                self.assertIsNone(parsed.verdict)
        incomplete = "\n".join(map(json.dumps, good[:5]))
        self.assertEqual(codex_cli.parse_event_stream(incomplete, 0).status, "operational_unknown")
        timed_out = codex_cli.parse_event_stream('{bad-json', None, timed_out=True)
        self.assertEqual(timed_out.status, "operational_unknown")
        self.assertIn("malformed_json", timed_out.protocol_violations)

    def test_duplicate_json_keys_are_never_valid_and_failure_precedence_holds(self):
        finals = (
            '{"verdict":"FAIL","verdict":"PASS","reason":"ok"}',
            '{"verdict":"PASS","verdict":"FAIL","reason":"ok"}',
            '{"verdict":"PASS","reason":"first","reason":"second"}',
            '{"verdict":"PASS","reason":"second","reason":"first"}',
            '{"verdict":"PASS","reason":"ok","nested":{"x":1,"x":2}}',
        )
        for final in finals:
            with self.subTest(final=final):
                raw = event_stream(final)
                result = codex_cli.parse_event_stream(raw, 0)
                self.assertEqual((result.status, result.verdict), ("invalid_output", None))
                self.assertEqual(codex_cli.parse_event_stream(raw, 1).status, "operational_unknown")
                self.assertEqual(codex_cli.parse_event_stream(raw, None, timed_out=True).status, "operational_unknown")
                projected = evidence.project_stdout(raw.encode("utf-8"))
                self.assertEqual(codex_cli.parse_event_stream(projected.decode("utf-8"), 0).status, result.status)
        final_event = json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": '{"verdict":"PASS","reason":"ok"}'}})
        prefix = '{"type":"thread.started"}\n{"type":"turn.started"}\n'
        malformed_events = (
            '{"type":"error","type":"turn.completed"}',
            '{"type":"turn.completed","type":"error"}',
            '{"type":"item.completed","item":{"type":"command_execution","type":"reasoning"}}',
            '{"type":"item.completed","item":{"type":"reasoning","type":"command_execution"}}',
            '{"type":"item.completed","item":{"type":"reasoning","id":"a","id":"b"}}',
            '{"type":"item.completed","item":{"type":"reasoning","id":"b","id":"a"}}',
        )
        for event in malformed_events:
            with self.subTest(event=event):
                raw = prefix + final_event + "\n" + event + "\n"
                result = codex_cli.parse_event_stream(raw, 0)
                self.assertEqual((result.status, result.verdict), ("protocol_invalid", None))
                self.assertIn("malformed_json", result.protocol_violations)
                self.assertEqual(codex_cli.parse_event_stream(raw, 1).status, "operational_unknown")
                self.assertEqual(codex_cli.parse_event_stream(raw, None, timed_out=True).status, "operational_unknown")
                projected = evidence.project_stdout(raw.encode("utf-8"))
                self.assertEqual(codex_cli.parse_event_stream(projected.decode("utf-8"), 0).status, result.status)

    def test_native_composition_capture_and_timeout_precedence(self):
        TASK_TMP.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="cli with spaces-", dir=TASK_TMP) as temporary:
            base = Path(temporary)
            cwd = base / "judge"
            cwd.mkdir()
            marker = "STUDY-CANARY-SECRET"
            calls = []
            stderr = b"x" * 9000 + b"terminal-sentinel " + marker.encode()
            def fake_native(argv, prompt, working_directory, capture_dir, timeout, env):
                calls.append((argv, prompt, working_directory, capture_dir, timeout, env))
                stdout = capture_dir / "stdout.bin"
                error = capture_dir / "stderr.bin"
                stdout.write_bytes(b'{"type":')
                error.write_bytes(stderr)
                return NativeResult(None, True, True, True, 0, "wait_wrapper", "wrapper_released", "TIMEOUT",
                                    stdout, error, capture_dir / "terminal.json", capture_dir / "process.json")
            with patch.object(codex_cli, "TASK_TMP", base), \
                    patch.object(codex_cli, "find_executable", return_value=r"C:\Program Files\codex.exe"), \
                    patch.object(codex_cli, "run_native", side_effect=fake_native), \
                    patch.dict(os.environ, {"OPENAI_API_KEY": "private-key"}):
                result = codex_cli.run_codex("prompt", cwd, 30, marker=marker)
            self.assertEqual(result.status, "operational_unknown")
            self.assertTrue(result.timed_out)
            self.assertEqual((result.failed_step, result.fault_code), ("wait_wrapper", "TIMEOUT"))
            self.assertIn("malformed_json", result.protocol_violations)
            self.assertIn("marker_echo", result.protocol_violations)
            self.assertTrue(result.marker_echo)
            self.assertEqual(result.stderr_capture.byte_count, len(stderr))
            self.assertEqual(result.stderr_capture.sha256, hashlib.sha256(stderr).hexdigest())
            self.assertTrue(result.stderr_capture.truncated)
            self.assertIn(b"terminal-sentinel", result.stderr_capture.tail)
            self.assertLessEqual(len(result.stderr_capture.head), codex_cli.DIAGNOSTIC_BYTES)
            self.assertLessEqual(len(result.stderr_capture.tail), codex_cli.DIAGNOSTIC_BYTES)
            argv, sent_prompt, actual_cwd, capture_dir, timeout, env = calls[0]
            self.assertEqual(sent_prompt, "prompt")
            self.assertEqual(actual_cwd, cwd.resolve())
            self.assertEqual(timeout, 30)
            self.assertNotIn("OPENAI_API_KEY", env)
            self.assertFalse(capture_dir.is_relative_to(cwd))
            self.assertEqual(argv[0], r"C:\Program Files\codex.exe")

    def test_native_success_requires_clean_custody_and_no_marker(self):
        TASK_TMP.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="cli-success-", dir=TASK_TMP) as temporary:
            base = Path(temporary)
            cwd = base / "judge"
            cwd.mkdir()
            def fake_native(argv, prompt, working_directory, capture_dir, timeout, env):
                stdout, stderr = capture_dir / "stdout.bin", capture_dir / "stderr.bin"
                stdout.write_text(event_stream('{"verdict":"PASS","reason":"ok"}'), encoding="utf-8")
                stderr.write_bytes(b"")
                return NativeResult(0, False, True, False, 0, None, "terminal_read", None,
                                    stdout, stderr, capture_dir / "terminal.json", capture_dir / "process.json")
            with patch.object(codex_cli, "TASK_TMP", base), patch.object(codex_cli, "find_executable", return_value="codex"), \
                    patch.object(codex_cli, "run_native", side_effect=fake_native):
                result = codex_cli.run_codex("prompt", cwd, 30)
            self.assertEqual((result.status, result.verdict), ("valid", "PASS"))
            self.assertTrue(result.cleanup_proven)
            self.assertEqual(result.active_processes_final, 0)

    def test_native_unproven_custody_and_missing_stdout_are_unknown(self):
        TASK_TMP.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="cli-failure-", dir=TASK_TMP) as temporary:
            base = Path(temporary)
            cwd = base / "judge"
            cwd.mkdir()
            def fake_native(argv, prompt, working_directory, capture_dir, timeout, env):
                stdout, stderr = capture_dir / "stdout.bin", capture_dir / "stderr.bin"
                stderr.write_bytes(b"terminal diagnostic")
                return NativeResult(0, False, False, True, None, "cleanup_job", "wrapper_exited", "QUERY_FAILED",
                                    stdout, stderr, capture_dir / "terminal.json", capture_dir / "process.json")
            with patch.object(codex_cli, "TASK_TMP", base), patch.object(codex_cli, "find_executable", return_value="codex"), \
                    patch.object(codex_cli, "run_native", side_effect=fake_native):
                result = codex_cli.run_codex("prompt", cwd, 30)
            self.assertEqual(result.status, "operational_unknown")
            self.assertIsNone(result.verdict)
            self.assertEqual((result.failed_step, result.fault_code), ("cleanup_job", "QUERY_FAILED"))
            self.assertIsNone(result.stdout_capture)
            self.assertEqual(result.stderr_capture.byte_count, len(b"terminal diagnostic"))
            self.assertIsNone(result.marker_echo)

    def test_inspection_has_finite_timeout(self):
        completed = CompletedProcess([], 0, "", "Logged in using ChatGPT")
        with patch.object(codex_cli, "find_executable", return_value="codex"), \
                patch.object(codex_cli.subprocess, "run", return_value=completed) as run:
            self.assertTrue(codex_cli.chatgpt_login_status())
        self.assertEqual(run.call_args.kwargs["timeout"], codex_cli.INSPECTION_TIMEOUT_SECONDS)


if __name__ == "__main__":
    unittest.main()
