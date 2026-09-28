"""Export RenderDoc per-render-target blend fields for selected frame events.

Set KIANA_BLEND_CONFIG to a JSON file with capture, event_ids and output.
Run through run_bundled_renderdoc_python.ps1.
"""

import json
import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] /
                       "release-next/win-unpacked/resources/kiana-runtime/pymodules"))
import renderdoc as rd


def fields(value):
    result = {}
    for key in dir(value):
        if key.startswith("_") or key in ("acquire", "append", "disown", "next", "own", "this", "thisown"):
            continue
        try:
            item = getattr(value, key)
            if not callable(item):
                result[key] = item if isinstance(item, (bool, int, float, str)) else str(item)
        except Exception:
            pass
    return result


def enum_name(enum_type, value):
    for name in dir(enum_type):
        if name.startswith("_"):
            continue
        try:
            if int(getattr(enum_type, name)) == int(value):
                return name
        except Exception:
            pass
    return str(value)


_config_path = os.environ.get("KIANA_BLEND_CONFIG") or (sys.argv[1] if len(sys.argv) > 1 else None)
if not _config_path:
    raise RuntimeError("Pass the blend config path as a script argument")
config = json.load(open(_config_path, encoding="utf-8"))
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
        pipe = controller.GetPipelineState()
        blends = []
        for blend in pipe.GetColorBlends():
            item = fields(blend)
            item["colorBlend"] = fields(blend.colorBlend)
            item["alphaBlend"] = fields(blend.alphaBlend)
            for channel in ("colorBlend", "alphaBlend"):
                for factor in ("source", "destination"):
                    item[channel][factor + "Name"] = enum_name(rd.BlendMultiplier, item[channel][factor])
            blends.append(item)
        report["events"].append({"eventId": eid,
                                 "independentBlend": pipe.IsIndependentBlendingEnabled(),
                                 "colorBlends": blends})
    report["ok"] = True
except Exception:
    report["error"] = traceback.format_exc()
finally:
    if controller:
        controller.Shutdown()
    if capture:
        capture.Shutdown()
    with open(config["output"], "w", encoding="utf-8") as out:
        json.dump(report, out, indent=2, ensure_ascii=False)
sys.exit(0 if report["ok"] else 1)
