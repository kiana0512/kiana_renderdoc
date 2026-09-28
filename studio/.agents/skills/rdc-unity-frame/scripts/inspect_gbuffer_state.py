"""Probe rasterizer, depth/stencil and blend state at selected RDC draws."""

import json
import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "release-next/win-unpacked/resources/kiana-runtime/pymodules"))
import renderdoc as rd


def describe(value, depth=0):
    if depth > 3:
        return str(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (tuple, list)) or hasattr(value, "__iter__") and not isinstance(value, dict):
        try:
            return [describe(v, depth + 1) for v in list(value)[:8]]
        except Exception:
            pass
    result = {}
    for name in dir(value):
        if name.startswith("_") or name in ("acquire", "append", "disown", "next", "own", "this", "thisown"):
            continue
        try:
            field = getattr(value, name)
            if callable(field):
                continue
            result[name] = describe(field, depth + 1)
        except Exception:
            pass
    return result or str(value)


config_path = sys.argv[1] if len(sys.argv) > 1 else os.environ["KIANA_STATE_CONFIG"]
config = json.load(open(config_path, encoding="utf-8"))
report = {"events": [], "ok": False}
capture = controller = None
try:
    capture = rd.OpenCaptureFile()
    status = capture.OpenFile(config["capture"], "rdc", None)
    if not status.OK():
        raise RuntimeError(status.Message())
    status, controller = capture.OpenCapture(rd.ReplayOptions(), None)
    if not status.OK():
        raise RuntimeError(status.Message())
    for eid in config["event_ids"]:
        controller.SetFrameEvent(eid, True)
        d3d = controller.GetD3D11PipelineState()
        pipe = controller.GetPipelineState()
        item = {"eventId": eid, "d3dFields": [x for x in dir(d3d) if not x.startswith("_")],
                "pipeFields": [x for x in dir(pipe) if not x.startswith("_")]}
        for name in ("rasterizer", "outputMerger", "RS", "OM"):
            if hasattr(d3d, name):
                item[name] = describe(getattr(d3d, name))
        report["events"].append(item)
    report["ok"] = True
except Exception:
    report["error"] = traceback.format_exc()
finally:
    if controller:
        controller.Shutdown()
    if capture:
        capture.Shutdown()
    with open(config["output"], "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
sys.exit(0 if report["ok"] else 1)
