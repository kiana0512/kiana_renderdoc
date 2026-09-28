"""Export per-pixel RT write history from an independent RenderDoc replay.

Use run_bundled_renderdoc_python.ps1 with KIANA_PIXEL_HISTORY_CONFIG pointing
to JSON containing capture, resource_id, pixels and output.
"""

import json
import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] /
                       "release-next/win-unpacked/resources/kiana-runtime/pymodules"))
import renderdoc as rd


def colour(value):
    return [float(v) for v in value.col.floatValue[:4]] if value else None


config_path = os.environ.get("KIANA_PIXEL_HISTORY_CONFIG") or (sys.argv[1] if len(sys.argv) > 1 else None)
if not config_path:
    raise RuntimeError("Pass pixel history config path")
config = json.loads(Path(config_path).read_text(encoding="utf-8"))
report = {"capture": config["capture"], "resourceId": int(config["resource_id"]), "pixels": []}
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
    report["matchingTextures"] = [
        {"resourceId": str(tex.resourceId),
         "width": int(tex.width), "height": int(tex.height)}
        for tex in controller.GetTextures()
        if str(tex.resourceId).endswith("::" + str(config["resource_id"]))]
    texture = rd.ResourceId()
    texture.id = int(config["resource_id"])
    for x, y in config["pixels"]:
        item = {"x": x, "y": y}
        try:
            mods = controller.PixelHistory(texture, int(x), int(y), rd.Subresource(0, 0, 0), rd.CompType.Typeless)
            item["modifications"] = [
                {"eventId": int(mod.eventId),
                 "primitiveId": int(mod.primitiveID),
                 "preColour": colour(mod.preMod),
                 "postColour": colour(mod.postMod),
                 "fields": [name for name in dir(mod) if not name.startswith("_")]}
                for mod in mods
            ]
        except Exception:
            item["error"] = traceback.format_exc()
        report["pixels"].append(item)
except Exception:
    report["error"] = traceback.format_exc()
finally:
    if controller:
        controller.Shutdown()
    if capture:
        capture.Shutdown()
    Path(config["output"]).write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
