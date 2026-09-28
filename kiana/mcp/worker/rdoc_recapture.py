"""Run inside Kiana's embedded Python and recapture one offline GFXR replay."""
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


config = json.loads(Path(os.environ["KIANA_NSIGHT_BRIDGE_CONFIG"]).read_text(encoding="utf-8"))
output = Path(config["output"]).resolve()
replayer = Path(config["replayer"]).resolve()
source = Path(config["source"]).resolve()
state = {"scope": "offline GFXReconstruct recapture", "captures": [], "messages": []}
started = time.monotonic()


def save_state():
    state["elapsed_seconds"] = round(time.monotonic() - started, 2)
    (output / "recapture-result.json").write_text(json.dumps(state, indent=2), encoding="utf-8")


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
    if replayer.name.lower() != "gfxrecon-replay.exe" or not replayer.is_file():
        raise ValueError("Only the bundled offline gfxrecon-replay.exe is accepted")
    if source.suffix.lower() != ".gfxr" or not source.is_file():
        raise ValueError("Only an existing .gfxr input is accepted")
    output.mkdir(parents=True, exist_ok=True)
    rd.SetDebugLogFile(str(output / "renderdoc-debug.log"))
    args = ["--force-windowed-origin", "32000,32000", "--log-file",
            str(output / "gfxrecon-replay.log"), str(source)]
    options = rd.CaptureOptions()
    options.allowFullscreen = False
    result = rd.ExecuteAndInject(str(replayer), str(replayer.parent),
                                 subprocess.list2cmdline(args), [],
                                 str(output / "recapture"), options, False)
    state["launch_result"] = str(result.result)
    state["ident"] = result.ident
    if result.result != rd.ResultCode.Succeeded:
        raise RuntimeError(str(result.result))
    target = rd.CreateTargetControl("", result.ident, "Kiana Nsight bridge", False)
    if target is None:
        raise RuntimeError("No target control connection")
    state["pid"] = target.GetPID()
    state["status"] = "waiting_for_capture"
    save_state()
    # This handle owns only the newly-created offline replay helper. It never searches
    # for, attaches to, or terminates the original game process.
    handle = kernel.OpenProcess(0x100000 | 0x1000 | 1, False, target.GetPID())
    target.QueueCapture(1, 1)
    deadline = time.monotonic() + int(config.get("timeout_seconds", 300))
    while target.Connected() and time.monotonic() < deadline:
        message = target.ReceiveMessage(None)
        if message.type != rd.TargetControlMessageType.Noop:
            state["messages"].append({"type": str(message.type), "api": target.GetAPI()})
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
        if kernel.WaitForSingleObject(handle, 2000) == 258:
            # The GUI-subsystem GFXR player waits for a console key after replay.
            state["offline_helper_terminated"] = bool(kernel.TerminateProcess(handle, 0))
            kernel.WaitForSingleObject(handle, 3000)
        code = wintypes.DWORD()
        if kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
            state["helper_exit_code"] = code.value
        kernel.CloseHandle(handle)
    state["rdc_files"] = [
        {"path": str(path), "bytes": path.stat().st_size}
        for path in output.glob("*.rdc")
    ]
    state["status"] = ("capture_saved" if state["captures"] and state["rdc_files"]
                       and "error" not in state else "failed")
    save_state()

sys.exit(0 if state["status"] == "capture_saved" else 1)
