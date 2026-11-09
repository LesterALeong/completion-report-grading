import hashlib
import http.server
import json
import os
import socket
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

from study import ollama_worker as worker
from study.protocol import TASK_TMP
from study.windows_job import run_native


HELPER = Path(__file__).parent / "fixtures" / "ollama_http_helper.py"


def request_bytes(model=worker.MODEL):
    request = {
        "model": model, "messages": [{"role": "user", "content": "INERT TEST ONLY: café"}],
        "stream": False, "tools": [], "format": worker.SCHEMA, "think": False,
        "keep_alive": "60s", "options": worker.OPTIONS,
    }
    return json.dumps(request, ensure_ascii=False, indent=1).encode("utf-8")


class RequestTests(unittest.TestCase):
    def test_fixed_request_and_refusals(self):
        raw = request_bytes()
        worker.validate_request(raw)
        for old, new in [(b'"stream": false', b'"stream": 0'),
                         (b'"think": false', b'"think": true'),
                         (b'"role": "user"', b'"role": "system"'),
                         (b'"num_thread": 2', b'"num_thread": true'),
                         (b'"minLength": 1', b'"minLength": true')]:
            with self.subTest(old=old), self.assertRaises(ValueError):
                worker.validate_request(raw.replace(old, new))
        with self.assertRaises(ValueError):
            worker.validate_request(raw.replace(b'"model":', b'"model": "duplicate", "model":'))


@unittest.skipUnless(os.name == "nt", "native Job Object requires Windows")
class NativeHTTPTests(unittest.TestCase):
    def setUp(self):
        TASK_TMP.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="http job with spaces ", dir=TASK_TMP)
        self.root = Path(self.temp.name)
        self.cwd = self.root / "judge directory"
        self.capture = self.root / "private capture"
        self.cwd.mkdir()
        self.capture.mkdir()
        self.received = []
        self.body = b"  \xc3\xa9\xff\n"
        self.mode = "complete"
        owner = self

        class Handler(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def do_POST(self):
                data = self.rfile.read(int(self.headers["Content-Length"]))
                owner.received.append((self.path, data))
                if b"INERT TEST ONLY" not in data:
                    self.send_error(400)
                    return
                if owner.mode == "timeout":
                    time.sleep(1)
                    return
                body = owner.body if owner.mode != "oversize" else b"x" * (worker.LIMIT + 1)
                self.send_response(503 if owner.mode == "error" else 200)
                self.send_header("Content-Length", str(len(body) + (5 if owner.mode == "incomplete" else 0)))
                self.send_header("Connection", "close")
                self.end_headers()
                try:
                    if owner.mode == "oversize":
                        # The final write is one byte; do not buffer it behind the preceding bulk transfer.
                        self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                    for offset in range(0, len(body), 65536):
                        self.wfile.write(body[offset:offset + 65536])
                except (BrokenPipeError, ConnectionResetError):
                    pass
                self.close_connection = True

            def log_message(self, *args):
                pass

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.assertNotEqual(self.server.server_port, 11434)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def run_worker(self, timeout=3):
        path = self.capture / "http.json"
        raw = request_bytes("inert-test-only-no-model")
        argv = [sys.executable, "-I", "-S", "-B", str(HELPER.resolve()), str(self.server.server_port),
                "--http-metadata", str(path), "--timeout-seconds", str(timeout)]
        result = run_native(argv, raw.decode("utf-8"), self.cwd, self.capture, timeout + 3)
        self.assertTrue(result.cleanup_proven)
        self.assertFalse(result.forced_cleanup)
        self.assertEqual(self.received, [(worker.ROUTE, raw)],
                         (result, result.stderr_path.read_bytes(), path.read_bytes() if path.exists() else None))
        with socket.create_connection(self.server.server_address, timeout=1):
            pass
        facts = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(facts["request_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(facts["request_bytes"], len(raw))
        body = result.stdout_path.read_bytes()
        self.assertEqual(facts["body_sha256"], hashlib.sha256(body).hexdigest())
        self.assertEqual(facts["body_bytes"], len(body))
        return result, facts, body

    def test_complete_exact_binary(self):
        result, facts, body = self.run_worker()
        self.assertEqual((result.returncode, facts["http_status"], facts["body_complete"]), (0, 200, True))
        self.assertEqual(body, self.body)
        self.assertFalse(facts["daemon_completion_uncertain"])

    def test_empty(self):
        self.body = b""
        result, facts, body = self.run_worker()
        self.assertEqual((result.returncode, facts["body_complete"], body), (0, True, b""))

    def test_http_error_preserves_body(self):
        self.mode = "error"
        result, facts, body = self.run_worker()
        self.assertEqual((result.returncode, facts["http_status"], body), (0, 503, self.body))

    def test_incomplete(self):
        self.mode = "incomplete"
        result, facts, body = self.run_worker()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(body, self.body)
        self.assertFalse(facts["body_complete"])
        self.assertTrue(facts["daemon_completion_uncertain"])

    def test_oversize(self):
        self.mode = "oversize"
        result, facts, body = self.run_worker(timeout=15)
        self.assertEqual((result.returncode, facts["fault_code"], len(body)), (1, "BODY_TOO_LARGE", worker.LIMIT + 1))
        self.assertTrue(facts["daemon_completion_uncertain"])

    def test_timeout(self):
        self.mode = "timeout"
        result, facts, _ = self.run_worker(timeout=0.2)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(facts["failed_step"], "response_headers")
        self.assertTrue(facts["daemon_completion_uncertain"])


if __name__ == "__main__":
    unittest.main()
