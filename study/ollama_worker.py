"""Isolated, bounded HTTP transport for one frozen Ollama request."""

import argparse
import hashlib
import http.client
import json
import math
import sys
import time
from pathlib import Path


HOST = "127.0.0.1"
PORT = 11434
ROUTE = "/api/chat"
LIMIT = 8 * 1024 * 1024
MODEL = "qwen3.5:9b-q4_K_M"
SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["PASS", "FAIL", "INDETERMINATE"]},
        "reason": {"type": "string", "minLength": 1, "maxLength": 300},
    },
    "required": ["verdict", "reason"],
    "additionalProperties": False,
}
OPTIONS = {"temperature": 0, "seed": 20261109, "num_ctx": 4096, "num_predict": 512, "num_thread": 2}


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def validate_request(raw):
    """Refuse any request that differs from the approved fixed controls."""
    if len(raw) > LIMIT:
        raise ValueError("request too large")
    request = json.loads(raw.decode("utf-8"), object_pairs_hook=_object,
                         parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    if not isinstance(request, dict) or set(request) != {
        "model", "messages", "stream", "tools", "format", "think", "keep_alive", "options"
    }:
        raise ValueError("invalid request keys")
    messages = request["messages"]
    if (request["model"] != MODEL or request["stream"] is not False or request["think"] is not False
            or request["tools"] != [] or json.dumps(request["format"], sort_keys=True) != json.dumps(SCHEMA, sort_keys=True)
            or request["keep_alive"] != "60s"
            or not isinstance(messages, list) or len(messages) != 1
            or not isinstance(messages[0], dict) or set(messages[0]) != {"role", "content"}
            or messages[0]["role"] != "user" or not isinstance(messages[0]["content"], str)):
        raise ValueError("invalid request controls")
    options = request["options"]
    if (not isinstance(options, dict) or set(options) != set(OPTIONS)
            or any(type(options[key]) is not int or options[key] != value for key, value in OPTIONS.items())):
        raise ValueError("invalid request options")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--http-metadata", required=True)
    parser.add_argument("--timeout-seconds", required=True, type=float)
    args = parser.parse_args()
    if not math.isfinite(args.timeout_seconds) or not 0 < args.timeout_seconds <= 180:
        return 2
    path = Path(args.http_metadata)
    if not path.is_absolute() or path.resolve().is_relative_to(Path.cwd().resolve()):
        return 2
    try:
        metadata = path.open("x", encoding="utf-8")
    except OSError:
        return 2

    facts = {
        "schema_version": 1, "endpoint": f"http://{HOST}:{PORT}", "route": ROUTE,
        "request_sha256": None, "request_bytes": 0, "http_status": None,
        "body_complete": False, "body_sha256": hashlib.sha256(b"").hexdigest(), "body_bytes": 0,
        "dispatched": False, "daemon_completion_uncertain": False,
        "failed_step": None, "last_completed_step": "metadata_created", "fault_code": None,
    }
    connection = None
    step = "read_request"
    digest = hashlib.sha256()
    deadline = time.monotonic() + args.timeout_seconds
    try:
        raw = sys.stdin.buffer.read(LIMIT + 1)
        facts["request_bytes"] = len(raw)
        facts["request_sha256"] = hashlib.sha256(raw).hexdigest()
        facts["last_completed_step"] = "request_read"
        step = "validate_request"
        validate_request(raw)
        facts["last_completed_step"] = "request_validated"
        step = "connect"
        connection = http.client.HTTPConnection(HOST, PORT, timeout=max(0.001, deadline - time.monotonic()))
        connection.connect()
        sock = connection.sock
        facts["last_completed_step"] = "connected"
        step = "dispatch"
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("request deadline")
        sock.settimeout(remaining)
        facts["dispatched"] = True
        connection.request("POST", ROUTE, body=raw, headers={"Content-Type": "application/json"})
        facts["last_completed_step"] = "request_dispatched"
        step = "response_headers"
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("response deadline")
        sock.settimeout(remaining)
        response = connection.getresponse()
        facts["http_status"] = response.status
        facts["last_completed_step"] = "headers_received"
        step = "response_body"
        while True:
            if response.isclosed():
                if response.length not in (None, 0):
                    raise http.client.IncompleteRead(b"", response.length)
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("response deadline")
            sock.settimeout(remaining)
            chunk = response.read1(min(65536, LIMIT + 1 - facts["body_bytes"]))
            if not chunk:
                if response.length not in (None, 0):
                    raise http.client.IncompleteRead(b"", response.length)
                break
            sys.stdout.buffer.write(chunk)
            digest.update(chunk)
            facts["body_bytes"] += len(chunk)
            if facts["body_bytes"] > LIMIT:
                raise ValueError("response too large")
        sys.stdout.buffer.flush()
        facts["body_complete"] = True
        facts["last_completed_step"] = "body_received"
    except (OSError, ValueError, UnicodeError, http.client.HTTPException) as error:
        facts["failed_step"] = step
        facts["fault_code"] = "BODY_TOO_LARGE" if step == "response_body" and facts["body_bytes"] > LIMIT else type(error).__name__
        facts["daemon_completion_uncertain"] = facts["dispatched"]
    finally:
        if connection is not None:
            connection.close()
        facts["body_sha256"] = digest.hexdigest()
        with metadata:
            json.dump(facts, metadata, sort_keys=True, separators=(",", ":"))
    return 1 if facts["failed_step"] else 0


if __name__ == "__main__":
    sys.exit(main())
