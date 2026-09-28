import json
import os
import sys
from pathlib import Path

paths = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Kiana RenderDoc/pymodules",
    Path(__file__).resolve().parents[4]
    / "release-next/win-unpacked/resources/kiana-runtime/pymodules",
]
sys.path.insert(0, str(next(p for p in paths if (p / "renderdoc.pyd").is_file())))
import renderdoc as rd


def describe(value, depth=0):
    if depth > 5:
        return str(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)) or (
        hasattr(value, "__iter__") and not isinstance(value, dict)
    ):
        try:
            return [describe(item, depth + 1) for item in list(value)]
        except Exception:
            pass
    result = {}
    for name in dir(value):
        if name.startswith("_") or name in {
            "acquire", "append", "disown", "next", "own", "this", "thisown"
        }:
            continue
        try:
            field = getattr(value, name)
            if callable(field):
                continue
            result[name] = describe(field, depth + 1)
        except Exception:
            pass
    return result or str(value)


cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
cap = rd.OpenCaptureFile()
status = cap.OpenFile(cfg["capture"], "rdc", None)
if not status.OK():
    raise RuntimeError(status.Message())
status, controller = cap.OpenCapture(rd.ReplayOptions(), None)
if not status.OK():
    raise RuntimeError(status.Message())

events = []
try:
    for event_id in cfg["event_ids"]:
        controller.SetFrameEvent(event_id, True)
        pipe = controller.GetPipelineState()
        d3d = controller.GetD3D12PipelineState()
        item = {
            "eventId": event_id,
            "pipeFields": [x for x in dir(pipe) if not x.startswith("_")],
            "d3d12Fields": [x for x in dir(d3d) if not x.startswith("_")],
        }
        for method in (
            "GetRasterState", "GetDepthTestState", "GetStencilFaces",
            "GetDepthTarget",
        ):
            try:
                item[method] = describe(getattr(pipe, method)())
            except Exception as exc:
                item[method] = {"error": repr(exc)}
        try:
            outputs = pipe.GetOutputTargets()
            item["outputTargets"] = [describe(outputs[index]) for index in range(len(outputs))]
        except Exception as exc:
            item["outputTargets"] = {"error": repr(exc)}
        try:
            blends = pipe.GetColorBlends()
            item["GetColorBlends"] = [
                {
                    "fields": [x for x in dir(blends[index]) if not x.startswith("_")],
                    "value": describe(blends[index]),
                }
                for index in range(len(blends))
            ]
        except Exception as exc:
            item["GetColorBlends"] = {"error": repr(exc)}
        try:
            item["GetViewport0"] = describe(pipe.GetViewport(0))
            item["GetScissor0"] = describe(pipe.GetScissor(0))
        except Exception as exc:
            item["viewportError"] = repr(exc)
        try:
            samplers = pipe.GetSamplers(rd.ShaderStage.Pixel)
            item["pixelSamplers"] = [describe(samplers[index]) for index in range(len(samplers))]
        except Exception as exc:
            item["samplerError"] = repr(exc)
        try:
            resources = pipe.GetReadOnlyResources(rd.ShaderStage.Pixel)
            item["pixelReadOnlyResources"] = [describe(resources[index]) for index in range(len(resources))]
        except Exception as exc:
            item["resourceError"] = repr(exc)
        for name in ("rasterizer", "depthStencil", "outputMerger", "RS", "OM"):
            if hasattr(d3d, name):
                item["d3d12." + name] = describe(getattr(d3d, name))
        events.append(item)
finally:
    controller.Shutdown()
    cap.Shutdown()

Path(cfg["output"]).write_text(
    json.dumps({"events": events}, indent=2), encoding="utf-8"
)
