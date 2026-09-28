"""Run inside Kiana's Python 3.6 and write a compact RDC verification report."""
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback

import renderdoc as rd


config = json.loads(Path(os.environ["KIANA_NSIGHT_VERIFY_CONFIG"]).read_text(encoding="utf-8"))
capture_path = Path(config["capture"]).resolve()
result_path = Path(config["result"]).resolve()
report = {"capture": str(capture_path), "ok": False}
capture = None
controller = None


def flatten(actions):
    for action in actions:
        yield action
        for child in flatten(action.children):
            yield child


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


try:
    capture = rd.OpenCaptureFile()
    status = capture.OpenFile(str(capture_path), "rdc", None)
    if not status.OK():
        raise RuntimeError(status.Message())
    status, controller = capture.OpenCapture(rd.ReplayOptions(), None)
    if not status.OK():
        raise RuntimeError(status.Message())
    actions = list(flatten(controller.GetRootActions()))
    draws = [a for a in actions if a.flags & rd.ActionFlags.Drawcall]
    dispatches = [a for a in actions if a.flags & rd.ActionFlags.Dispatch]
    resources = controller.GetResources()
    shader_ids = set()
    stages = [rd.ShaderStage.Vertex, rd.ShaderStage.Hull, rd.ShaderStage.Domain,
              rd.ShaderStage.Geometry, rd.ShaderStage.Pixel, rd.ShaderStage.Compute]
    for action in draws + dispatches:
        controller.SetFrameEvent(action.eventId, False)
        pipeline = controller.GetPipelineState()
        for stage in stages:
            shader_id = int(pipeline.GetShader(stage))
            if shader_id:
                shader_ids.add(shader_id)
    props = controller.GetAPIProperties()
    frame = controller.GetFrameInfo()
    report.update({
        "ok": bool(controller.GetFatalErrorStatus().OK()),
        "api": str(props.pipelineType),
        "renderer": str(props.localRenderer),
        "frame_number": frame.frameNumber,
        "action_count": len(actions),
        "draw_count": len(draws),
        "dispatch_count": len(dispatches),
        "texture_count": len(controller.GetTextures()),
        "buffer_count": len(controller.GetBuffers()),
        "resource_count": len(resources),
        "shader_count": len(shader_ids),
        "last_event_id": max([a.eventId for a in actions] or [0]),
        "bytes": capture_path.stat().st_size,
        "sha256": sha256(capture_path),
        "fatal_error": str(controller.GetFatalErrorStatus()),
    })
except Exception:
    report["error"] = traceback.format_exc()
finally:
    if controller:
        controller.Shutdown()
    if capture:
        capture.Shutdown()
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

sys.exit(0 if report.get("ok") else 1)
