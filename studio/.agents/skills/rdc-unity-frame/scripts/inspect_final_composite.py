"""Inspect frame 38112 final-composite draw bindings and PS constants."""
import json
import struct
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "release-next/win-unpacked/resources/kiana-runtime/pymodules"))
import renderdoc as rd

cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
report = {"events": [], "ok": False}
capture = controller = None
try:
    capture = rd.OpenCaptureFile()
    status = capture.OpenFile(cfg["capture"], "rdc", None)
    if not status.OK():
        raise RuntimeError(status.Message())
    status, controller = capture.OpenCapture(rd.ReplayOptions(), None)
    if not status.OK():
        raise RuntimeError(status.Message())
    for eid in cfg["event_ids"]:
        event = {"eventId": eid}
        try:
            controller.SetFrameEvent(eid, True)
            pipe = controller.GetPipelineState()
            event["vertexShader"] = int(pipe.GetShader(rd.ShaderStage.Vertex))
            event["pixelShader"] = int(pipe.GetShader(rd.ShaderStage.Pixel))
            event["pixelResources"] = []
            for slot, binding in enumerate(pipe.GetReadOnlyResources(rd.ShaderStage.Pixel)):
                d = binding.descriptor
                if int(d.resource):
                    event["pixelResources"].append({"slot": slot, "resourceId": int(d.resource),
                                                    "type": str(d.type)})
            event["pixelConstantBuffers"] = []
            for slot, binding in enumerate(pipe.GetConstantBlocks(rd.ShaderStage.Pixel, False)):
                d = binding.descriptor
                if not int(d.resource):
                    continue
                raw = controller.GetBufferData(d.resource, int(d.byteOffset), min(256, int(d.byteSize)))
                event["pixelConstantBuffers"].append({"slot": slot, "resourceId": int(d.resource),
                    "float4s": [list(struct.unpack_from("<4f", raw, i)) for i in range(0, len(raw)-15, 16)]})
            mesh = controller.GetPostVSData(eid, 0, rd.MeshDataStage.VSOut)
            event["postVSByEID"] = {"indices": int(mesh.numIndices), "stride": int(mesh.vertexByteStride)}
            mesh = controller.GetPostVSData(0, 0, rd.MeshDataStage.VSOut)
            event["postVSByZero"] = {"indices": int(mesh.numIndices), "stride": int(mesh.vertexByteStride)}
        except Exception:
            event["error"] = traceback.format_exc()
        report["events"].append(event)
    report["ok"] = all("error" not in e for e in report["events"])
except Exception:
    report["error"] = traceback.format_exc()
finally:
    if controller:
        controller.Shutdown()
    if capture:
        capture.Shutdown()
    Path(cfg["output"]).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
sys.exit(0 if report["ok"] else 1)
