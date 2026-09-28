"""Export pixel-stage read-only buffer bindings and their selected bytes.

Run in Kiana's bundled RenderDoc Python with KIANA_STRUCTURED_CONFIG set to
JSON containing capture, event_ids and output. The standalone replay leaves
the user's current Kiana GUI event unchanged.
"""

import json
import os
import struct
import sys
import traceback
from pathlib import Path

import renderdoc as rd


config = json.loads(Path(os.environ["KIANA_STRUCTURED_CONFIG"]).read_text(encoding="utf-8"))
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
        event = {"eventId": int(event_id), "pixelReadOnlyBuffers": []}
        try:
            controller.SetFrameEvent(int(event_id), True)
            pipe = controller.GetPipelineState()
            for slot, used in enumerate(pipe.GetReadOnlyResources(rd.ShaderStage.Pixel)):
                descriptor = used.descriptor
                if str(descriptor.type) != "DescriptorType.Buffer":
                    continue
                resource = descriptor.resource
                item = {
                    "slot": slot,
                    "resourceId": int(resource),
                    "byteOffset": int(descriptor.byteOffset),
                    "byteSize": int(descriptor.byteSize),
                    "elementByteSize": int(descriptor.elementByteSize),
                }
                if item["resourceId"]:
                    count = min(item["elementByteSize"], item["byteSize"])
                    raw = controller.GetBufferData(resource, item["byteOffset"], count)
                    item["firstElementHex"] = bytes(raw).hex()
                    item["firstElementFloat4"] = [
                        list(struct.unpack_from("<4f", raw, i))
                        for i in range(0, len(raw) - 15, 16)
                    ]
                event["pixelReadOnlyBuffers"].append(item)
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
