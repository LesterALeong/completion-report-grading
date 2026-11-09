"""Blocked Windows Job member: start the requested child only after release."""

import json
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    release = sys.stdin.buffer.readline(4097)
    if not release.endswith(b"\n") or len(release) > 4096:
        return 2
    control = json.loads(Path(release[:-1].decode("utf-8")).read_text(encoding="utf-8"))
    terminal = Path(control["terminal_path"])
    metadata = Path(control["metadata_path"])
    step = "open_capture"
    try:
        with Path(control["stdout_path"]).open("xb") as stdout, Path(control["stderr_path"]).open("xb") as stderr:
            step = "launch_child"
            child = subprocess.Popen(
                control["argv"], stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                cwd=control["cwd"], shell=False,
            )
            metadata.write_text(json.dumps({"wrapper_pid": os.getpid(), "cli_pid": child.pid}), encoding="utf-8")
            step = "communicate"
            child.communicate(input=control["prompt"].encode("utf-8"))
            record = {"returncode": child.returncode, "failed_step": None, "fault_code": None}
    except Exception as error:
        record = {"returncode": None, "failed_step": step, "fault_code": type(error).__name__}
    terminal.write_text(json.dumps(record), encoding="utf-8")
    return 0 if record["failed_step"] is None else 1


if __name__ == "__main__":
    sys.exit(main())
