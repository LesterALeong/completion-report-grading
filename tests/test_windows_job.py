import ctypes
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from study import windows_job
from study.protocol import TASK_TMP
from study.windows_job import run_native


HELPER = Path(__file__).parent / "fixtures" / "transport_helper.py"


@unittest.skipUnless(os.name == "nt", "native Job Object requires Windows")
class WindowsJobTests(unittest.TestCase):
    def setUp(self):
        TASK_TMP.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="native job with spaces ", dir=TASK_TMP)
        self.root = Path(self.temp.name)
        self.cwd = self.root / "judge directory"
        self.capture = self.root / "private capture"
        self.cwd.mkdir()
        self.capture.mkdir()
        self.sentinel = subprocess.Popen(
            [sys.executable, "-I", "-S", "-B", str(HELPER.resolve()), "descendant"],
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

    def tearDown(self):
        if self.sentinel.poll() is None:
            self.sentinel.terminate()
        self.sentinel.wait(timeout=5)
        self.temp.cleanup()

    def run_helper(self, mode, timeout=5):
        pid_path = self.root / "descendant pid.txt"
        argv = [sys.executable, "-I", "-S", "-B", str(HELPER.resolve()), mode, str(pid_path)]
        result = run_native(argv, "hello", self.cwd, self.capture, timeout, cleanup_timeout_seconds=5)
        self.assertIsNone(self.sentinel.poll(), "unrelated sentinel was terminated")
        return result, pid_path

    def assert_dead(self, pid):
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.OpenProcess(0x00100000, False, pid)
        if handle:
            try:
                self.assertEqual(kernel.WaitForSingleObject(handle, 5000), 0)
            finally:
                kernel.CloseHandle(handle)
        else:
            self.assertEqual(ctypes.get_last_error(), 87, "failed to inspect task-owned process")

    def test_clean_success_and_private_capture(self):
        result, _ = self.run_helper("normal")
        self.assertEqual(result.returncode, 0)
        self.assertFalse(result.timed_out)
        self.assertFalse(result.forced_cleanup)
        self.assertTrue(result.cleanup_proven)
        self.assertEqual(result.active_processes_final, 0)
        self.assertIsNone(result.failed_step)
        self.assertEqual(result.stdout_path.read_bytes(), b"received:hello\r\n")
        self.assertEqual(result.stderr_path.read_bytes(), b"diagnostic\r\n")
        self.assertIn("cli_pid", json.loads(result.metadata_path.read_text(encoding="utf-8")))

    def test_timeout_terminates_child_and_descendant(self):
        started = time.monotonic()
        result, pid_path = self.run_helper("timeout", timeout=1)
        self.assertLess(time.monotonic() - started, 8)
        self.assertTrue(result.timed_out)
        self.assertTrue(result.forced_cleanup)
        self.assertTrue(result.cleanup_proven)
        self.assertEqual(result.active_processes_final, 0)
        self.assertEqual((result.failed_step, result.fault_code), ("wait_wrapper", "TIMEOUT"))
        self.assert_dead(int(pid_path.read_text(encoding="utf-8")))
        self.assert_dead(json.loads(result.metadata_path.read_text(encoding="utf-8"))["cli_pid"])

    def test_lingering_descendant_is_forced_and_not_success(self):
        result, pid_path = self.run_helper("lingering")
        self.assertEqual(result.returncode, 0)
        self.assertTrue(result.forced_cleanup)
        self.assertTrue(result.cleanup_proven)
        self.assertEqual(result.active_processes_final, 0)
        self.assertEqual((result.failed_step, result.fault_code), ("cleanup_job", "LINGERING_PROCESS"))
        self.assert_dead(int(pid_path.read_text(encoding="utf-8")))

    def test_child_launch_failure_has_finite_terminal_reason(self):
        result = run_native([str(self.root / "missing executable.exe")], "", self.cwd, self.capture, 5)
        self.assertIsNone(result.returncode)
        self.assertEqual((result.failed_step, result.fault_code), ("launch_child", "FileNotFoundError"))
        self.assertTrue(result.cleanup_proven)
        self.assertFalse(result.forced_cleanup)
        self.assertIsNone(self.sentinel.poll())

    def test_assignment_failure_kills_only_inert_wrapper_before_release(self):
        kernel, structures = windows_job._windows_api()
        wrapper_pids = []
        real_popen = subprocess.Popen

        class AssignmentFault:
            def __getattr__(self, name):
                return getattr(kernel, name)

            def AssignProcessToJobObject(self, *args):
                ctypes.set_last_error(5)
                return 0

        def record_wrapper(*args, **kwargs):
            process = real_popen(*args, **kwargs)
            wrapper_pids.append(process.pid)
            return process

        with patch.object(windows_job, "_windows_api", return_value=(AssignmentFault(), structures)), patch.object(windows_job.subprocess, "Popen", side_effect=record_wrapper):
            result, _ = self.run_helper("normal")
        self.assertEqual(result.failed_step, "assign_wrapper")
        self.assertIsNone(result.returncode)
        self.assertTrue(result.cleanup_proven)
        self.assertFalse(result.metadata_path.exists(), "payload child started before Job assignment")
        self.assertEqual(len(wrapper_pids), 1)
        self.assert_dead(wrapper_pids[0])

    def test_release_failure_terminates_assigned_blocked_wrapper(self):
        real_popen = subprocess.Popen
        wrapper_pids = []

        class BrokenWriter:
            def __init__(self, raw):
                self.raw = raw

            @property
            def closed(self):
                return self.raw.closed

            def write(self, value):
                raise BrokenPipeError("injected release fault")

            def close(self):
                return self.raw.close()

        class WrapperProxy:
            def __init__(self, process):
                self.process = process
                self.stdin = BrokenWriter(process.stdin)

            def __getattr__(self, name):
                return getattr(self.process, name)

        def break_release(*args, **kwargs):
            process = real_popen(*args, **kwargs)
            wrapper_pids.append(process.pid)
            return WrapperProxy(process)

        with patch.object(windows_job.subprocess, "Popen", side_effect=break_release):
            result, _ = self.run_helper("normal")
        self.assertEqual((result.failed_step, result.fault_code), ("release_wrapper", "BrokenPipeError"))
        self.assertTrue(result.cleanup_proven)
        self.assertEqual(result.active_processes_final, 0)
        self.assertFalse(result.metadata_path.exists())
        self.assert_dead(wrapper_pids[0])

    def test_capture_collision_is_retained_as_finite_failure(self):
        real_popen = subprocess.Popen

        def collide_after_validation(*args, **kwargs):
            process = real_popen(*args, **kwargs)
            (self.capture / "stderr.bin").write_bytes(b"preexisting capture sentinel")
            return process

        with patch.object(windows_job.subprocess, "Popen", side_effect=collide_after_validation):
            result, _ = self.run_helper("normal")
        self.assertEqual((result.failed_step, result.fault_code), ("open_capture", "FileExistsError"))
        self.assertIsNone(result.returncode)
        self.assertTrue(result.cleanup_proven)
        self.assertEqual(result.stderr_path.read_bytes(), b"preexisting capture sentinel")
        self.assertFalse(result.metadata_path.exists())

    def test_cleanup_query_failure_refuses_proof_and_job_close_kills_descendant(self):
        kernel, structures = windows_job._windows_api()

        class QueryFault:
            def __getattr__(self, name):
                return getattr(kernel, name)

            def QueryInformationJobObject(self, *args):
                ctypes.set_last_error(5)
                return 0

        started = time.monotonic()
        with patch.object(windows_job, "_windows_api", return_value=(QueryFault(), structures)):
            result, pid_path = self.run_helper("lingering")
        self.assertLess(time.monotonic() - started, 8)
        self.assertEqual(result.failed_step, "cleanup_job")
        self.assertFalse(result.cleanup_proven)
        self.assertIsNone(result.active_processes_final)
        self.assert_dead(int(pid_path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
