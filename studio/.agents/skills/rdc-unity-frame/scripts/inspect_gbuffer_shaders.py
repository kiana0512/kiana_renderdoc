"""Export shader signatures and DXBC disassembly for selected RDC events.

Run inside Kiana's bundled qrenderdoc Python with KIANA_SHADER_CONFIG JSON.
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


config_path = sys.argv[1] if len(sys.argv) > 1 else os.environ["KIANA_SHADER_CONFIG"]
config = json.load(open(config_path, encoding="utf-8"))
out = Path(config["output_dir"])
out.mkdir(parents=True, exist_ok=True)
report = {"events": [], "ok": False}
capture = controller = None
try:
    capture = rd.OpenCaptureFile()
    status = capture.OpenFile(config["capture"], "rdc", None)
    if not status.OK():
        raise RuntimeError(status.Message())
    status, controller = capture.OpenCapture(rd.ReplayOptions(), None)
    if not status.OK():
        raise RuntimeError(status.Message())
    for eid in config["event_ids"]:
        item = {"eventId": eid, "stages": {}}
        controller.SetFrameEvent(eid, True)
        pipe = controller.GetPipelineState()
        for label, stage in (("vertex", rd.ShaderStage.Vertex),
                             ("fragment", rd.ShaderStage.Pixel)):
            shader_id = pipe.GetShader(stage)
            if not int(shader_id):
                continue
            entry = controller.GetShaderEntryPoints(shader_id)[0]
            reflection = controller.GetShader(rd.ResourceId(), shader_id, entry)
            info = {"resourceId": int(shader_id)}
            if reflection:
                info["inputSignature"] = [{"name": str(x.semanticName), "index": int(x.semanticIndex),
                                             "reg": int(x.regIndex), "count": int(x.compCount)}
                                            for x in reflection.inputSignature]
                info["outputSignature"] = [{"name": str(x.semanticName), "index": int(x.semanticIndex),
                                              "reg": int(x.regIndex), "count": int(x.compCount)}
                                             for x in reflection.outputSignature]
                try:
                    disasm = controller.DisassembleShader(rd.ResourceId(), reflection, "")
                    path = out / ("EID%d-%s.txt" % (eid, label))
                    path.write_text(disasm, encoding="utf-8")
                    info["disassembly"] = str(path)
                except Exception:
                    info["disassemblyError"] = traceback.format_exc()
                    info["disassemblyDoc"] = str(controller.DisassembleShader.__doc__)
            item["stages"][label] = info
        report["events"].append(item)
    report["ok"] = True
except Exception:
    report["error"] = traceback.format_exc()
finally:
    if controller:
        controller.Shutdown()
    if capture:
        capture.Shutdown()
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
sys.exit(0 if report["ok"] else 1)
