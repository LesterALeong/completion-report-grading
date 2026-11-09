"""Bounded Windows Job custody for a single task-owned transport process tree."""

from __future__ import annotations

import ctypes
import json
import math
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .protocol import TASK_TMP


@dataclass(frozen=True)
class NativeResult:
    """Private capture locations and finite transport/custody facts.

    A usable child result requires returncode zero, no timeout or forced cleanup,
    cleanup_proven, and a terminal record. Capture files are private evidence.
    """

    returncode: int | None
    timed_out: bool
    cleanup_proven: bool
    forced_cleanup: bool
    active_processes_final: int | None
    failed_step: str | None
    last_completed_step: str
    fault_code: str | None
    stdout_path: Path
    stderr_path: Path
    terminal_path: Path
    metadata_path: Path


def _windows_api() -> tuple[Any, Any]:
    from ctypes import wintypes

    class IoCounters(ctypes.Structure):
        _fields_ = [(name, ctypes.c_ulonglong) for name in (
            "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
            "ReadTransferCount", "WriteTransferCount", "OtherTransferCount",
        )]

    class BasicLimits(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_longlong), ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class ExtendedLimits(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", BasicLimits), ("IoInfo", IoCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    class Accounting(ctypes.Structure):
        _fields_ = [
            ("TotalUserTime", ctypes.c_longlong), ("TotalKernelTime", ctypes.c_longlong),
            ("ThisPeriodTotalUserTime", ctypes.c_longlong), ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
            ("TotalPageFaultCount", wintypes.DWORD), ("TotalProcesses", wintypes.DWORD),
            ("ActiveProcesses", wintypes.DWORD), ("TotalTerminatedProcesses", wintypes.DWORD),
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]
    kernel.CreateJobObjectW.restype = wintypes.HANDLE
    kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD]
    kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD, wintypes.LPVOID]
    kernel.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    return kernel, (ExtendedLimits, Accounting)


def _owned_path(path: Path) -> Path:
    resolved = Path(path).resolve()
    if not resolved.is_relative_to(TASK_TMP.resolve()):
        raise ValueError("paths must be under the task temporary root")
    return resolved


def run_native(
    argv: list[str], prompt: str, cwd: Path, capture_dir: Path, timeout_seconds: float,
    cleanup_timeout_seconds: float = 5, env: dict[str, str] | None = None,
) -> NativeResult:
    """Run an argv under an assigned-before-release Job; never delete the judge cwd."""
    if os.name != "nt":
        raise RuntimeError("native transport requires Windows")
    cwd = _owned_path(cwd)
    capture_dir = _owned_path(capture_dir)
    if not cwd.is_dir() or not capture_dir.is_dir() or capture_dir.is_relative_to(cwd):
        raise ValueError("existing capture directory must be outside existing judge directory")
    if not argv or timeout_seconds <= 0 or cleanup_timeout_seconds <= 0:
        raise ValueError("argv and positive finite timeouts are required")
    if not all(isinstance(arg, str) for arg in argv):
        raise ValueError("argv must contain strings")
    if not math.isfinite(timeout_seconds) or not math.isfinite(cleanup_timeout_seconds):
        raise ValueError("timeouts must be finite")

    paths = {name: capture_dir / name for name in ("stdout.bin", "stderr.bin", "terminal.json", "process.json", "control.json")}
    if any(path.exists() for path in paths.values()):
        raise FileExistsError("capture files must be fresh")
    control = {
        "argv": argv, "prompt": prompt, "cwd": str(cwd),
        "stdout_path": str(paths["stdout.bin"]), "stderr_path": str(paths["stderr.bin"]),
        "terminal_path": str(paths["terminal.json"]), "metadata_path": str(paths["process.json"]),
    }
    payload = json.dumps(control, ensure_ascii=True).encode("utf-8")
    if len(payload) > 8 * 1024 * 1024 or len(os.fsencode(str(paths["control.json"]))) > 4000:
        raise ValueError("control payload or path exceeds bound")
    with paths["control.json"].open("xb") as stream:
        stream.write(payload)

    kernel, structures = _windows_api()
    limits_type, accounting_type = structures
    job = None
    wrapper = None
    assigned = False
    timed_out = False
    forced = False
    cleanup_proven = False
    active = None
    failed_step = None
    fault_code = None
    last = "control_created"
    step = "create_job"
    returncode = None
    deadline = time.monotonic() + timeout_seconds
    try:
        job = kernel.CreateJobObjectW(None, None)
        if not job:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = limits_type()
        limits.BasicLimitInformation.LimitFlags = 0x2000
        step = "configure_job"
        if not kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            raise ctypes.WinError(ctypes.get_last_error())
        last = "job_configured"
        step = "launch_wrapper"
        wrapper = subprocess.Popen(
            [sys.executable, "-I", "-S", "-B", str(Path(__file__).with_name("transport_worker.py").resolve())],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            cwd=str(cwd), env=env, shell=False, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        last = "wrapper_started"
        step = "assign_wrapper"
        if not kernel.AssignProcessToJobObject(job, int(wrapper._handle)):
            raise ctypes.WinError(ctypes.get_last_error())
        assigned = True
        last = "wrapper_assigned"
        step = "release_wrapper"
        wrapper.stdin.write((str(paths["control.json"]) + "\n").encode("utf-8"))
        wrapper.stdin.close()
        last = "wrapper_released"
        step = "wait_wrapper"
        try:
            wrapper.wait(timeout=max(0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            timed_out = True
            failed_step, fault_code = step, "TIMEOUT"
        else:
            last = "wrapper_exited"
            step = "read_terminal"
            record = json.loads(paths["terminal.json"].read_text(encoding="utf-8"))
            returncode = record["returncode"]
            if record["failed_step"] is not None:
                failed_step, fault_code = record["failed_step"], record["fault_code"]
            elif wrapper.returncode != 0:
                failed_step, fault_code = step, "WRAPPER_NONZERO"
            else:
                last = "terminal_read"
    except Exception as error:
        failed_step, fault_code = step, type(error).__name__
    finally:
        if wrapper is not None and not assigned and wrapper.poll() is None:
            try:
                wrapper.kill()
                wrapper.wait(timeout=cleanup_timeout_seconds)
            except (OSError, subprocess.TimeoutExpired) as error:
                if failed_step is None:
                    failed_step, fault_code = "cleanup_wrapper", type(error).__name__
        if job:
            cleanup_deadline = time.monotonic() + cleanup_timeout_seconds
            try:
                accounting = accounting_type()
                if not kernel.QueryInformationJobObject(job, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), None):
                    raise ctypes.WinError(ctypes.get_last_error())
                active = int(accounting.ActiveProcesses)
                # Windows can report an exited wrapper briefly after its wait handle signals.
                settle_deadline = min(cleanup_deadline, time.monotonic() + 0.25)
                while active and not timed_out and wrapper is not None and wrapper.poll() is not None:
                    if time.monotonic() >= settle_deadline:
                        break
                    time.sleep(min(0.01, max(0, settle_deadline - time.monotonic())))
                    if not kernel.QueryInformationJobObject(job, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), None):
                        raise ctypes.WinError(ctypes.get_last_error())
                    active = int(accounting.ActiveProcesses)
                if active:
                    forced = True
                    if failed_step is None:
                        failed_step, fault_code = "cleanup_job", "LINGERING_PROCESS"
                    if not kernel.TerminateJobObject(job, 1):
                        raise ctypes.WinError(ctypes.get_last_error())
                while active:
                    if time.monotonic() >= cleanup_deadline:
                        break
                    time.sleep(min(0.02, max(0, cleanup_deadline - time.monotonic())))
                    if not kernel.QueryInformationJobObject(job, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), None):
                        raise ctypes.WinError(ctypes.get_last_error())
                    active = int(accounting.ActiveProcesses)
                cleanup_proven = active == 0 and (wrapper is None or assigned or wrapper.poll() is not None)
                if wrapper is not None and assigned:
                    try:
                        wrapper.wait(timeout=max(0, cleanup_deadline - time.monotonic()))
                    except subprocess.TimeoutExpired:
                        cleanup_proven = False
                if not cleanup_proven and failed_step is None:
                    failed_step, fault_code = "cleanup_job", "ACTIVE_PROCESSES"
            except Exception as error:
                if failed_step is None:
                    failed_step, fault_code = "cleanup_job", type(error).__name__
            finally:
                kernel.CloseHandle(job)
        if wrapper is not None and wrapper.stdin is not None and not wrapper.stdin.closed:
            wrapper.stdin.close()
    return NativeResult(
        returncode, timed_out, cleanup_proven, forced, active, failed_step, last, fault_code,
        paths["stdout.bin"], paths["stderr.bin"], paths["terminal.json"], paths["process.json"],
    )
