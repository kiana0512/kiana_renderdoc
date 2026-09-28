"""Run inside Kiana's embedded Python and capture a launched application.

The worker is intentionally a small, separate process so a target crash or a
graphics-hook failure cannot take down the MCP server.  It only launches the
explicit executable supplied in the config and only terminates that child.
"""

import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import renderdoc as rd


config = json.loads(Path(os.environ["KIANA_DIRECT_CAPTURE_CONFIG"]).read_text(encoding="utf-8"))
output = Path(config["output"]).resolve()
executable = Path(config["executable"]).resolve()
working_dir = Path(config.get("working_dir") or executable.parent).resolve()
arguments = list(config.get("arguments") or [])
frame = int(config.get("frame", 300))
timeout_seconds = int(config.get("timeout_seconds", 180))
terminate_after_capture = bool(config.get("terminate_after_capture", False))
state = {"scope": "direct application capture", "captures": [], "messages": []}
started = time.monotonic()


def save_state():
    state["elapsed_seconds"] = round(time.monotonic() - started, 2)
    (output / "direct-capture-result.json").write_text(
        json.dumps(state, indent=2), encoding="utf-8"
    )


target = None
handle = None
kernel = ctypes.WinDLL("kernel32", use_last_error=True)
kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel.OpenProcess.restype = wintypes.HANDLE
kernel.CloseHandle.argtypes = [wintypes.HANDLE]
kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]

try:
    if not executable.is_file():
        raise ValueError("Executable does not exist")
    if not working_dir.is_dir():
        raise ValueError("Working directory does not exist")
    if frame < 1:
        raise ValueError("Capture frame must be positive")

    output.mkdir(parents=True, exist_ok=True)
    rd.SetDebugLogFile(str(output / "renderdoc-debug.log"))

    env = []
    for name, value in (config.get("environment") or {}).items():
        mod = rd.EnvironmentModification()
        mod.name = str(name)
        mod.value = str(value)
        mod.mod = rd.EnvMod.Set
        mod.sep = rd.EnvSep.NoSep
        env.append(mod)

    options = rd.CaptureOptions()
    options.allowFullscreen = False
    options.hookIntoChildren = bool(config.get("hook_children", False))
    result = rd.ExecuteAndInject(
        str(executable),
        str(working_dir),
        subprocess.list2cmdline(arguments),
        env,
        str(output / "capture"),
        options,
        False,
    )
    state["launch_result"] = str(result.result)
    state["ident"] = result.ident
    if result.result != rd.ResultCode.Succeeded:
        raise RuntimeError(str(result.result))

    target = rd.CreateTargetControl("", result.ident, "Kiana direct capture", False)
    if target is None:
        raise RuntimeError("No target control connection")

    state["pid"] = target.GetPID()
    state["status"] = "waiting_for_capture"
    save_state()
    # SYNCHRONIZE | QUERY_LIMITED_INFORMATION | TERMINATE. This handle refers
    # only to the newly-created child returned by RenderDoc target control.
    handle = kernel.OpenProcess(0x100000 | 0x1000 | 1, False, target.GetPID())
    target.QueueCapture(frame, 1)
    deadline = time.monotonic() + timeout_seconds
    while target.Connected() and time.monotonic() < deadline:
        message = target.ReceiveMessage(None)
        if message.type != rd.TargetControlMessageType.Noop:
            state["messages"].append(
                {"type": str(message.type), "api": target.GetAPI()}
            )
            save_state()
        if message.type == rd.TargetControlMessageType.NewCapture:
            state["captures"].append(str(message.newCapture.path))
            break

    if not state["captures"]:
        raise RuntimeError("No completed capture before target disconnect or timeout")
except Exception:
    state["error"] = traceback.format_exc()
finally:
    if target:
        target.Shutdown()
    if handle:
        if terminate_after_capture and kernel.WaitForSingleObject(handle, 2000) == 258:
            state["child_terminated"] = bool(kernel.TerminateProcess(handle, 0))
            kernel.WaitForSingleObject(handle, 3000)
        elif not terminate_after_capture:
            state["child_terminated"] = False
        code = wintypes.DWORD()
        if kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
            # STILL_ACTIVE is expected when the caller asked to keep the game open.
            state["child_exit_code"] = None if code.value == 259 else code.value
        kernel.CloseHandle(handle)
    state["rdc_files"] = [
        {"path": str(path), "bytes": path.stat().st_size}
        for path in output.glob("*.rdc")
    ]
    state["status"] = (
        "capture_saved"
        if state["captures"] and state["rdc_files"] and "error" not in state
        else "failed"
    )
    save_state()

sys.exit(0 if state["status"] == "capture_saved" else 1)
