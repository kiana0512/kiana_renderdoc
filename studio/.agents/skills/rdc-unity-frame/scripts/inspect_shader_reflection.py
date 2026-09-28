import json
import os
import sys
from pathlib import Path

paths = [Path(os.environ.get("LOCALAPPDATA", "")) / "Kiana RenderDoc/pymodules",
         Path(__file__).resolve().parents[4] / "release-next/win-unpacked/resources/kiana-runtime/pymodules"]
sys.path.insert(0, str(next(p for p in paths if (p / "renderdoc.pyd").is_file())))
import renderdoc as rd

cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
cap = rd.OpenCaptureFile()
s = cap.OpenFile(cfg["capture"], "rdc", None)
if not s.OK(): raise RuntimeError(s.Message())
s, c = cap.OpenCapture(rd.ReplayOptions(), None)
if not s.OK(): raise RuntimeError(s.Message())
try:
    c.SetFrameEvent(cfg["event_id"], True)
    sid = c.GetPipelineState().GetShader(rd.ShaderStage.Pixel)
    entry = c.GetShaderEntryPoints(sid)[0]
    r = c.GetShader(rd.ResourceId(), sid, entry)
    result = {"reflectionFields": [x for x in dir(r) if not x.startswith("_")],
              "entryFields": [x for x in dir(entry) if not x.startswith("_")]}
    if cfg.get("raw_output"):
        raw = bytes(bytearray(r.rawBytes))
        Path(cfg["raw_output"]).write_bytes(raw)
        result["rawOutput"] = cfg["raw_output"]
        result["rawBytes"] = len(raw)
    for name in result["reflectionFields"]:
        try:
            value = getattr(r, name)
            if not callable(value) and isinstance(value, (str, int, float, bool)):
                result[name] = value
        except Exception:
            pass
    Path(cfg["output"]).write_text(json.dumps(result, indent=2), encoding="utf-8")
finally:
    c.Shutdown(); cap.Shutdown()
