"""Inert process tree used only by native supervisor tests."""

import os
import subprocess
import sys
import time
from pathlib import Path


def main() -> None:
    mode = sys.argv[1]
    if mode == "descendant":
        time.sleep(60)
    elif mode in {"timeout", "lingering"}:
        child = subprocess.Popen([sys.executable, "-I", "-S", "-B", __file__, "descendant"])
        Path(sys.argv[2]).write_text(str(child.pid), encoding="utf-8")
        if mode == "timeout":
            time.sleep(60)
    elif mode == "normal":
        print("received:" + sys.stdin.read())
        print("diagnostic", file=sys.stderr)
    else:
        os._exit(3)


if __name__ == "__main__":
    main()
