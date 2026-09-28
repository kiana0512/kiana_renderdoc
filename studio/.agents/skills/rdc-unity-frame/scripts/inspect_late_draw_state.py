"""Export exact VS object matrix and output state for late RDC draw events."""

import json
import os
import struct
import sys
import traceback
from pathlib import Path

runtime = Path(os.environ.get("LOCALAPPDATA", "")) / "Kiana RenderDoc/pymodules"
sys.path.insert(0, str(runtime))
import renderdoc as rd

config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
report = {"capture": config["capture"], "events": []}
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
        event = {"eventId": int(event_id)}
        try:
            controller.SetFrameEvent(int(event_id), True)
            pipeline = controller.GetPipelineState()
            blocks = pipeline.GetConstantBlocks(rd.ShaderStage.Vertex, False)
            binding = blocks[1].descriptor
            raw = controller.GetBufferData(binding.resource, int(binding.byteOffset), int(binding.byteSize))
            event["vsCb1FirstFloat4s"] = [list(struct.unpack_from("<4f", raw, i)) for i in range(0, min(len(raw), 160), 16)]
            event["colorBlends"] = [
                {
                    "enabled": bool(blend.enabled),
                    "color": {k: str(getattr(blend.colorBlend, k)) for k in ("source", "destination", "operation")},
                    "alpha": {k: str(getattr(blend.alphaBlend, k)) for k in ("source", "destination", "operation")},
                    "writeMask": int(blend.writeMask),
                }
                for blend in pipeline.GetColorBlends()
            ]
            event["depth"] = {k: str(getattr(pipeline.GetDepthTestState(), k)) for k in ("depthEnable", "depthWrites", "depthFunction")}
            event["stencilEnabled"] = bool(pipeline.IsStencilTestEnabled())
            event["raster"] = {k: str(getattr(pipeline.GetRasterState(), k)) for k in ("cullMode", "frontCCW")}
            textures = {str(t.resourceId): t for t in controller.GetTextures()}
            event["pixelTextures"] = []
            for slot, bound in enumerate(pipeline.GetReadOnlyResources(rd.ShaderStage.Pixel)):
                rid = str(bound.descriptor.resource)
                if rid == "ResourceId::Null()":
                    continue
                texture = textures.get(rid)
                event["pixelTextures"].append({
                    "slot": slot, "resourceId": rid,
                    "name": str(texture.name) if texture else "",
                    "width": int(texture.width) if texture else 0,
                    "height": int(texture.height) if texture else 0,
                    "format": str(texture.format) if texture else "",
                })
        except Exception:
            event["error"] = traceback.format_exc()
        report["events"].append(event)
finally:
    if controller:
        controller.Shutdown()
    if capture:
        capture.Shutdown()
Path(config["output"]).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
