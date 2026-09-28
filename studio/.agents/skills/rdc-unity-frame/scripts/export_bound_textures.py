"""Export selected RDC texture bindings as PNG in one replay process.

Usage: run_bundled_renderdoc_python.ps1 -ScriptPath THIS -ScriptArgs CONFIG.json
Config fields: capture, output_dir, textures [{resourceId, eventId}].
"""

import json
import os
import sys
import traceback
from pathlib import Path

for candidate in (
    Path(os.environ.get("LOCALAPPDATA", "")) / "Kiana RenderDoc/pymodules",
    Path(__file__).resolve().parents[4] / "release-next/win-unpacked/resources/kiana-runtime/pymodules",
):
    if (candidate / "renderdoc.pyd").is_file():
        sys.path.insert(0, str(candidate))
        break
import renderdoc as rd

config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
output = Path(config["output_dir"])
output.mkdir(parents=True, exist_ok=True)
report = {"capture": config["capture"], "textures": [], "ok": False}
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
    for entry in config["textures"]:
        rid = int(entry["resourceId"])
        item = {"resourceId": rid, "eventId": int(entry["eventId"])}
        try:
            destination = output / ("RID%d.png" % rid)
            controller.SetFrameEvent(item["eventId"], True)
            save = rd.TextureSave()
            save.resourceId = resources[rid]
            save.mip = 0
            save.destType = rd.FileType.PNG
            status = controller.SaveTexture(save, str(destination))
            if status.code != rd.ResultCode.Succeeded:
                raise RuntimeError(str(status))
            item["path"] = str(destination)
            item["bytes"] = destination.stat().st_size
        except Exception:
            item["error"] = traceback.format_exc()
        report["textures"].append(item)
    report["ok"] = all("error" not in item for item in report["textures"])
except Exception:
    report["error"] = traceback.format_exc()
finally:
    if controller:
        controller.Shutdown()
    if capture:
        capture.Shutdown()
    (output / "export-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
sys.exit(0 if report["ok"] else 1)
