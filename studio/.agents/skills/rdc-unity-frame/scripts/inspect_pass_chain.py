"""Inspect exact action/resource contracts for a RenderDoc event interval.

The report is intentionally based on the currently opened capture instead of
the generated reconstruction manifest. Resource IDs may change when a capture
is re-saved, while the event ordering and actual bindings remain authoritative.
"""

import json
import os
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


def resource_id(value):
    try:
        return int(value)
    except Exception:
        return 0


def descriptor_resource(binding):
    try:
        return resource_id(binding.descriptor.resource)
    except Exception:
        return 0


cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
report = {"capture": cfg["capture"], "range": [cfg["first"], cfg["last"]], "events": [], "ok": False}
capture = controller = None
try:
    capture = rd.OpenCaptureFile()
    status = capture.OpenFile(cfg["capture"], "rdc", None)
    if not status.OK():
        raise RuntimeError(status.Message())
    status, controller = capture.OpenCapture(rd.ReplayOptions(), None)
    if not status.OK():
        raise RuntimeError(status.Message())

    names = {resource_id(r.resourceId): r.name for r in controller.GetResources()}
    textures = {}
    for texture in controller.GetTextures():
        rid = resource_id(texture.resourceId)
        textures[rid] = {
            "name": names.get(rid, ""),
            "width": int(texture.width),
            "height": int(texture.height),
            "format": str(texture.format.Name()),
            "mips": int(texture.mips),
            "arraysize": int(texture.arraysize),
        }

    actions = []

    def walk(items):
        for action in items:
            if cfg["first"] <= action.eventId <= cfg["last"]:
                actions.append(action)
            walk(action.children)

    walk(controller.GetRootActions())
    for action in actions:
        eid = int(action.eventId)
        controller.SetFrameEvent(eid, True)
        pipe = controller.GetPipelineState()
        item = {
            "eventId": eid,
            "name": action.customName,
            "flags": str(action.flags),
            "indices": int(action.numIndices),
            "instances": int(action.numInstances),
            "dispatch": [int(v) for v in action.dispatchDimension],
            "shaders": {},
            "outputs": [],
            "depth": None,
            "readOnly": {},
            "readWrite": {},
        }
        for stage_name, stage in (("vs", rd.ShaderStage.Vertex), ("ps", rd.ShaderStage.Pixel),
                                  ("cs", rd.ShaderStage.Compute)):
            sid = resource_id(pipe.GetShader(stage))
            if sid:
                item["shaders"][stage_name] = {"id": sid, "name": names.get(sid, "")}

            read_only = []
            for slot, binding in enumerate(pipe.GetReadOnlyResources(stage)):
                rid = descriptor_resource(binding)
                if rid:
                    read_only.append({"slot": slot, "resource": textures.get(rid, {"name": names.get(rid, ""), "id": rid}), "id": rid})
            if read_only:
                item["readOnly"][stage_name] = read_only

            read_write = []
            for slot, binding in enumerate(pipe.GetReadWriteResources(stage)):
                rid = descriptor_resource(binding)
                if rid:
                    read_write.append({"slot": slot, "resource": textures.get(rid, {"name": names.get(rid, ""), "id": rid}), "id": rid})
            if read_write:
                item["readWrite"][stage_name] = read_write

        for slot, target in enumerate(pipe.GetOutputTargets()):
            rid = resource_id(target.resource)
            if rid:
                item["outputs"].append({"slot": slot, "id": rid, "resource": textures.get(rid, {"name": names.get(rid, "")})})
        depth = pipe.GetDepthTarget()
        depth_id = resource_id(depth.resource)
        if depth_id:
            item["depth"] = {"id": depth_id, "resource": textures.get(depth_id, {"name": names.get(depth_id, "")})}
        report["events"].append(item)
    report["ok"] = True
except Exception:
    report["error"] = traceback.format_exc()
finally:
    if controller:
        controller.Shutdown()
    if capture:
        capture.Shutdown()
    Path(cfg["output"]).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
sys.exit(0 if report["ok"] else 1)
