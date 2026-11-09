import copy
import hashlib
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from study import ollama
from study.data import load_protocol
from study.protocol import canonical_json


MODEL = "qwen3.5:9b-q4_K_M"


def envelope(content='{"verdict":"PASS","reason":"ok"}', **changes):
    value = {"model": MODEL, "done": True, "message": {"role": "assistant", "content": content}}
    value.update(changes)
    return canonical_json(value)


def facts(body):
    return {"schema_version": 1, "endpoint": ollama.ENDPOINT, "route": "/api/chat", "http_status": 200,
            "body_complete": True, "body_sha256": hashlib.sha256(body).hexdigest(), "body_bytes": len(body),
            "dispatched": True, "daemon_completion_uncertain": False, "failed_step": None,
            "terminal_exit": 0, "timed_out": False, "cleanup_proven": True, "forced_cleanup": False,
            "active_processes_final": 0, "native_failed_step": None}


class OllamaTests(unittest.TestCase):
    def test_request_and_static_identity(self):
        request = json.loads(ollama.build_request("hello"))
        self.assertEqual(request["messages"], [{"role": "user", "content": "hello"}])
        self.assertEqual(request["model"], MODEL)
        self.assertEqual({key: request[key] for key in ("stream", "tools", "think", "keep_alive", "options")},
                         load_protocol()["transport"]["request"])
        with patch.object(ollama, "_metadata_query", side_effect=AssertionError("network")):
            self.assertEqual(len(ollama.configuration_sha256()), 64)

    def test_completion_and_projection_precedence(self):
        body = envelope()
        baseline = facts(body)
        parsed = ollama.parse_response(body, baseline, MODEL)
        self.assertEqual((parsed.status, parsed.verdict, parsed.reason, parsed.event_count), ("valid", "PASS", "ok", 0))
        for key, value in (("terminal_exit", None), ("timed_out", True), ("cleanup_proven", False),
                           ("forced_cleanup", True), ("active_processes_final", None), ("http_status", 503),
                           ("body_complete", False), ("daemon_completion_uncertain", True),
                           ("body_sha256", "bad"), ("body_bytes", 1)):
            changed = dict(baseline, **{key: value})
            with self.subTest(key=key):
                self.assertEqual(ollama.parse_response(body, changed, MODEL).status, "operational_unknown")
                self.assertEqual(ollama.parse_projection(ollama.project_response(body, changed), MODEL).status, "operational_unknown")
        for done in (False, None, 1):
            invalid = envelope(done=done)
            self.assertEqual(ollama.parse_response(invalid, facts(invalid), MODEL).status, "operational_unknown")
        for invalid in (envelope(model="other"), envelope(error="bad"), b'{"done":true,"done":true}', b'\xff'):
            self.assertEqual(ollama.parse_response(invalid, facts(invalid), MODEL).status, "operational_unknown")

    def test_tool_thinking_and_inner_schema(self):
        for field, value in (("tool_calls", [{}]), ("tool_calls", {}), ("thinking", "secret"), ("thinking", None)):
            body = envelope(message={"role": "assistant", "content": '{"verdict":"PASS","reason":"ok"}', field: value})
            result = ollama.parse_response(body, facts(body), MODEL)
            self.assertEqual(result.status, "protocol_invalid")
            self.assertEqual(ollama.parse_projection(ollama.project_response(body, facts(body)), MODEL).status, result.status)
        for content in ('{}', '{"verdict":"PASS","reason":""}',
                        '{"verdict":"PASS","reason":"a","reason":"b"}',
                        '{"verdict":"PASS","reason":"' + 'x' * 301 + '"}'):
            body = envelope(content)
            self.assertEqual(ollama.parse_response(body, facts(body), MODEL).status, "invalid_output")
            self.assertEqual(ollama.parse_projection(ollama.project_response(body, facts(body)), MODEL).status, "invalid_output")

    def test_projection_redacts_reason(self):
        body = envelope('{"verdict":"PASS","reason":"email user@example.com"}')
        projected = ollama.project_response(body, facts(body))
        self.assertNotIn(b'user@example.com', projected)
        parsed = ollama.parse_projection(projected, MODEL)
        self.assertEqual((parsed.status, parsed.reason), ("valid", "email [email omitted]"))

    def test_native_adapter_joins_request_and_body(self):
        body = envelope()
        request = ollama.build_request("hello")
        metadata = {key: None for key in ollama.HTTP_KEYS}
        metadata.update({key: value for key, value in facts(body).items() if key in ollama.HTTP_KEYS})
        metadata.update(request_sha256=hashlib.sha256(request).hexdigest(), request_bytes=len(request),
                        last_completed_step="body_received")
        native = SimpleNamespace(returncode=0, timed_out=False, cleanup_proven=True, forced_cleanup=False,
                                 active_processes_final=0, failed_step=None, last_completed_step="child_exited",
                                 fault_code=None, stdout_path=Path("stdout"), stderr_path=Path("stderr"),
                                 terminal_path=Path("terminal"), metadata_path=Path("process"))
        capture = SimpleNamespace()
        original_read = Path.read_bytes

        def read(path):
            return canonical_json(metadata) if path.name == "http.json" else original_read(path)

        with patch.object(ollama, "validate_working_directory", return_value=Path("judge")), \
             patch.object(Path, "mkdir"), patch.object(Path, "read_bytes", read), \
             patch.object(ollama, "run_native", return_value=native) as run, \
             patch.object(ollama, "_capture", side_effect=[(capture, body, False), (capture, None, False)]):
            result = ollama.run_ollama("hello", "judge", 180)
        self.assertEqual((result.status, result.request_sha256, result.request_bytes),
                         ("valid", metadata["request_sha256"], len(request)))
        self.assertEqual(run.call_args.args[1].encode(), request)
        self.assertEqual(run.call_args.args[0][1:4], ["-I", "-S", "-B"])
        metadata["request_sha256"] = "wrong"
        with patch.object(ollama, "validate_working_directory", return_value=Path("judge")), \
             patch.object(Path, "mkdir"), patch.object(Path, "read_bytes", read), \
             patch.object(ollama, "run_native", return_value=native), \
             patch.object(ollama, "_capture", side_effect=[(capture, body, False), (capture, None, False)]):
            result = ollama.run_ollama("hello", "judge", 180)
        self.assertEqual(result.status, "operational_unknown")
        self.assertTrue(result.cleanup_proven)

    def test_runtime_exact_identity_and_mutations(self):
        expected = load_protocol()["transport"]["expected_runtime"]
        show = {key: None for key in expected["show_fields"]}
        show.update({key: copy.deepcopy(expected[key]) for key in ("thinking", "details", "parameters", "capabilities")})
        # Supply fixed fixture strings with hashes derived from these exact inputs.
        show["template"] = "fixture template"
        adjusted = copy.deepcopy(expected)
        adjusted["template_sha256"] = hashlib.sha256(show["template"].encode()).hexdigest()
        protocol = copy.deepcopy(load_protocol())
        protocol["transport"]["expected_runtime"] = adjusted
        responses = [{"version": adjusted["server_version"]}, {"models": [{"name": MODEL,
                     "digest": adjusted["digest"], "size": adjusted["size"]}]}, show]
        with patch.object(ollama, "load_protocol", return_value=protocol), patch.object(ollama, "_metadata_query", side_effect=responses):
            self.assertEqual(ollama.inspect_runtime()["observed"], adjusted)
        bad = copy.deepcopy(responses)
        bad[1]["models"][0]["digest"] = "bad"
        with patch.object(ollama, "load_protocol", return_value=protocol), patch.object(ollama, "_metadata_query", side_effect=bad):
            with self.assertRaises(ValueError):
                ollama.inspect_runtime()


if __name__ == "__main__":
    unittest.main()
