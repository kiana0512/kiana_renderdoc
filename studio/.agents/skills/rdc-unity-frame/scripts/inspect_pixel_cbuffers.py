"""Export pixel-stage constant-buffer float4 values from selected RDC events.

Run with Kiana's bundled qrenderdoc Python and KIANA_PIXEL_CB_CONFIG JSON.
The replay process is independent of the GUI's current event.
"""

import json
import os
import struct
import sys
import traceback
from pathlib import Path

_pymodule_candidates = [
    Path(__file__).resolve().parents[4] / "release-next/win-unpacked/resources/kiana-runtime/pymodules",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Kiana RenderDoc/pymodules",
]
_pymodules = next((path for path in _pymodule_candidates if (path / "renderdoc.pyd").is_file()), None)
if _pymodules is None:
    raise RuntimeError("Kiana RenderDoc Python module directory was not found")
sys.path.insert(0, str(_pymodules))
import renderdoc as rd


config_path = sys.argv[1] if len(sys.argv) > 1 else os.environ["KIANA_PIXEL_CB_CONFIG"]
config = json.loads(Path(config_path).read_text(encoding="utf-8"))
report = {"capture": config["capture"], "events": [], "ok": False}
capture = controller = None
try:
    capture = rd.OpenCaptureFile()
    status = capture.OpenFile(config["capture"], "rdc", None)
    if not status.OK():
        raise RuntimeError(status.Message())
    status, controller = capture.OpenCapture(rd.ReplayOptions(), None)
    if not status.OK():
        raise RuntimeError(status.Message())
    for event_id in config["event_ids"]:
        event = {"eventId": int(event_id), "pixelConstantBuffers": []}
        try:
            controller.SetFrameEvent(int(event_id), True)
            pipeline = controller.GetPipelineState()
            event["pixelShaderId"] = int(pipeline.GetShader(rd.ShaderStage.Pixel))
            for slot, binding in enumerate(pipeline.GetConstantBlocks(rd.ShaderStage.Pixel, False)):
                descriptor = binding.descriptor
                resource_id = descriptor.resource
                item = {
                    "slot": slot,
                    "resourceId": int(resource_id),
                    "byteOffset": int(descriptor.byteOffset),
                    "byteSize": int(descriptor.byteSize),
                }
                if int(resource_id):
                    raw = controller.GetBufferData(
                        resource_id, item["byteOffset"], item["byteSize"])
                    item["readBytes"] = len(raw)
                    item["float4s"] = [list(struct.unpack_from("<4f", raw, i))
                                       for i in range(0, len(raw) - 15, 16)]
                event["pixelConstantBuffers"].append(item)
        except Exception:
            event["error"] = traceback.format_exc()
        report["events"].append(event)
    report["ok"] = all("error" not in event for event in report["events"])
except Exception:
    report["error"] = traceback.format_exc()
finally:
    if controller:
        controller.Shutdown()
    if capture:
        capture.Shutdown()
    Path(config["output"]).write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
sys.exit(0 if report["ok"] else 1)
