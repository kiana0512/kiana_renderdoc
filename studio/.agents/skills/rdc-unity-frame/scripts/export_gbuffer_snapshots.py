"""Save a G-buffer attachment after selected RDC draw events in isolated replay."""

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


config_path = sys.argv[1] if len(sys.argv) > 1 else os.environ["KIANA_GBUFFER_SNAPSHOT_CONFIG"]
config = json.load(open(config_path, encoding="utf-8"))
out = Path(config["output_dir"])
out.mkdir(parents=True, exist_ok=True)
resource_ids = config.get("resource_ids", [config.get("resource_id")])
report = {"capture": config["capture"], "resourceIds": resource_ids,
          "events": [], "ok": False}
capture = controller = None
try:
    capture = rd.OpenCaptureFile()
    status = capture.OpenFile(config["capture"], "rdc", None)
    if not status.OK():
        raise RuntimeError(status.Message())
    status, controller = capture.OpenCapture(rd.ReplayOptions(), None)
    if not status.OK():
        raise RuntimeError(status.Message())
    resources = {int(resource.resourceId): resource.resourceId
                 for resource in controller.GetResources()}
    for rid in resource_ids:
        if int(rid) not in resources:
            raise ValueError("Texture resource ID absent: " + str(rid))
    for eid in config["event_ids"]:
        item = {"eventId": eid}
        try:
            controller.SetFrameEvent(int(eid), True)
            item["outputs"] = []
            for rid in resource_ids:
                target = out / ("EID%d-RID%d.png" % (eid, rid))
                save = rd.TextureSave()
                save.resourceId = resources[int(rid)]
                save.mip = 0
                save.destType = rd.FileType.PNG
                result = controller.SaveTexture(save, str(target))
                if result.code != rd.ResultCode.Succeeded:
                    raise RuntimeError(str(result))
                item["outputs"].append({"resourceId": rid, "path": str(target),
                                        "bytes": target.stat().st_size})
        except Exception:
            item["error"] = traceback.format_exc()
        report["events"].append(item)
    report["ok"] = all("error" not in x for x in report["events"])
except Exception:
    report["error"] = traceback.format_exc()
finally:
    if controller:
        controller.Shutdown()
    if capture:
        capture.Shutdown()
    (out / "snapshots.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
sys.exit(0 if report["ok"] else 1)
