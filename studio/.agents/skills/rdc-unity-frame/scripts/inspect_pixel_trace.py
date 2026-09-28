"""Trace selected RDC pixels through a PS, recording actual register values.

Set KIANA_PIXEL_TRACE_CONFIG to JSON with capture, event_id, pixels and output.
Run with run_bundled_renderdoc_python.ps1 in a separate process.
"""

import json
import os
import sys
import traceback
from pathlib import Path

_pymodules = Path(__file__).resolve().parents[4] / "release-next/win-unpacked/resources/kiana-runtime/pymodules"
if not (_pymodules / "renderdoc.pyd").exists():
    _pymodules = Path(os.environ["LOCALAPPDATA"]) / "Kiana RenderDoc/pymodules"
sys.path.insert(0, str(_pymodules))
import renderdoc as rd


def _variable(variable):
    if variable is None:
        return None
    result = {"name": getattr(variable, "name", ""),
              "type": str(getattr(variable, "type", ""))}
    value = getattr(variable, "value", None)
    if value is not None:
        for member in ("f32v", "u32v", "s32v"):
            try:
                result[member] = list(getattr(value, member))[:4]
            except Exception:
                pass
    return result


_config_path = os.environ.get("KIANA_PIXEL_TRACE_CONFIG") or (sys.argv[1] if len(sys.argv) > 1 else None)
if not _config_path:
    raise RuntimeError("Pass the trace config path as a script argument")
config = json.loads(Path(_config_path).read_text(encoding="utf-8"))
report = {"capture": config["capture"], "eventId": int(config["event_id"]), "pixels": [], "ok": False}
capture = controller = None
try:
    capture = rd.OpenCaptureFile()
    status = capture.OpenFile(config["capture"], "rdc", None)
    if not status.OK():
        raise RuntimeError(status.Message())
    status, controller = capture.OpenCapture(rd.ReplayOptions(), None)
    if not status.OK():
        raise RuntimeError(status.Message())
    controller.SetFrameEvent(int(config["event_id"]), True)
    for point in config["pixels"]:
        x, y = [int(value) for value in point]
        item = {"x": x, "y": y, "steps": []}
        try:
            inputs = rd.DebugPixelInputs()
            inputs.sample = 0
            inputs.primitive = 0xFFFFFFFF
            trace = controller.DebugPixel(x, y, inputs)
            if not trace or not trace.debugger:
                item["error"] = "No debugger trace for pixel"
            else:
                item["traceFields"] = [name for name in dir(trace) if not name.startswith("_")]
                item["inputs"] = [_variable(variable) for variable in trace.inputs]
                batch = controller.ContinueDebug(trace.debugger)
                while batch:
                    for state in batch:
                        if "stateFields" not in item:
                            item["stateFields"] = [name for name in dir(state) if not name.startswith("_")]
                        record = {"stepIndex": int(state.stepIndex),
                                  "nextInstruction": int(state.nextInstruction),
                                  "flags": str(state.flags)}
                        changes = getattr(state, "changes", None)
                        if changes:
                            record["changes"] = [
                                {"before": _variable(change.before),
                                 "after": _variable(change.after)}
                                for change in changes
                            ]
                        item["steps"].append(record)
                    batch = controller.ContinueDebug(trace.debugger)
                controller.FreeTrace(trace)
        except Exception:
            item["error"] = traceback.format_exc()
        report["pixels"].append(item)
    report["ok"] = all("error" not in item for item in report["pixels"])
except Exception:
    report["error"] = traceback.format_exc()
finally:
    if controller:
        controller.Shutdown()
    if capture:
        capture.Shutdown()
    Path(config["output"]).write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
