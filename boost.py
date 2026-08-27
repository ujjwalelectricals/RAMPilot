"""RAMPilot Step 3 - conservative Windows working-set boost.

This does NOT terminate applications, suspend them, or change startup/settings.
Windows may reclaim clean pages from a process working set; applications stay
running and Windows can bring pages back when needed.
"""

import ctypes
import os
import sys
from dataclasses import dataclass

import psutil


# PROCESS_QUERY_LIMITED_INFORMATION + PROCESS_SET_QUOTA
PROCESS_SET_QUOTA = 0x0100
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

# Windows API from psapi.dll. EmptyWorkingSet trims a process working set.
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True) if sys.platform == "win32" else None
_psapi = ctypes.WinDLL("psapi", use_last_error=True) if sys.platform == "win32" else None

if _kernel32:
    _kernel32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
    _kernel32.OpenProcess.restype = ctypes.c_void_p
    _kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    _kernel32.CloseHandle.restype = ctypes.c_int

if _psapi:
    _psapi.EmptyWorkingSet.argtypes = [ctypes.c_void_p]
    _psapi.EmptyWorkingSet.restype = ctypes.c_int


# Processes we should never touch. This is deliberately conservative.
PROTECTED = {
    "system", "system idle process", "registry", "smss.exe", "csrss.exe",
    "wininit.exe", "services.exe", "lsass.exe", "winlogon.exe",
    "dwm.exe", "fontdrvhost.exe", "memory compression", "secure system",
    "svchost.exe", "audiodg.exe", "msmpeng.exe", "sihost.exe",
    "explorer.exe", "searchhost.exe", "startmenuexperiencehost.exe",
    "shellexperiencehost.exe", "runtimebroker.exe", "taskhostw.exe",
    "applicationframehost.exe", "ctfmon.exe", "spoolsv.exe",
}


@dataclass
class BoostResult:
    attempted: int
    succeeded: int
    reclaimed_before: int
    reclaimed_after: int


def _is_protected(name: str) -> bool:
    normalized = name.strip().lower()
    return normalized in PROTECTED


def _trim_process(pid: int) -> bool:
    if not _kernel32 or not _psapi:
        return False
    handle = _kernel32.OpenProcess(
        PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_SET_QUOTA, False, pid
    )
    if not handle:
        return False
    try:
        return bool(_psapi.EmptyWorkingSet(handle))
    finally:
        _kernel32.CloseHandle(handle)


def boost() -> BoostResult:
    """Trim eligible, non-protected user processes without closing them."""
    if os.name != "nt":
        raise RuntimeError("RAMPilot Step 3 Boost currently requires Windows.")

    before = psutil.virtual_memory().available
    attempted = 0
    succeeded = 0

    current_pid = os.getpid()
    processes = []
    for process in psutil.process_iter(["pid", "name", "memory_info"]):
        try:
            pid = process.info["pid"]
            name = process.info["name"] or ""
            rss = process.info["memory_info"].rss
            if pid == current_pid or _is_protected(name):
                continue
            # Only attempt processes holding at least 100 MB.
            if rss < 100 * 1024 * 1024:
                continue
            processes.append((rss, pid, name))
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Start with the biggest working sets so the operation stays small.
    processes.sort(reverse=True)
    for _, pid, _ in processes[:20]:
        attempted += 1
        try:
            if _trim_process(pid):
                succeeded += 1
        except (OSError, PermissionError):
            continue

    after = psutil.virtual_memory().available
    return BoostResult(attempted, succeeded, before, after)
