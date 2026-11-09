"""Test-only bootstrap: substitute an inert ephemeral loopback endpoint."""

import importlib.util
import sys
from pathlib import Path


port = int(sys.argv[1])
if not 0 < port < 65536 or port == 11434:
    raise ValueError("inert test endpoint required")
worker_path = Path(__file__).resolve().parents[2] / "study" / "ollama_worker.py"
spec = importlib.util.spec_from_file_location("isolated_ollama_worker", worker_path)
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)
worker.PORT = port
worker.MODEL = "inert-test-only-no-model"
sys.argv = [str(worker_path), *sys.argv[2:]]
sys.exit(worker.main())
