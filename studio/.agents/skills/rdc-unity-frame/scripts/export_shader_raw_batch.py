import json
import hashlib
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


cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
output_dir = Path(cfg["output_dir"])
output_dir.mkdir(parents=True, exist_ok=True)

cap = rd.OpenCaptureFile()
status = cap.OpenFile(cfg["capture"], "rdc", None)
if not status.OK():
    raise RuntimeError(status.Message())
status, controller = cap.OpenCapture(rd.ReplayOptions(), None)
if not status.OK():
    raise RuntimeError(status.Message())

manifest = []
try:
    for event_id in cfg["event_ids"]:
        controller.SetFrameEvent(event_id, True)
        pipeline = controller.GetPipelineState()
        for stage, suffix in (
            (rd.ShaderStage.Vertex, "VS"),
            (rd.ShaderStage.Pixel, "PS"),
        ):
            shader_id = pipeline.GetShader(stage)
            if shader_id == rd.ResourceId.Null():
                manifest.append({"eventId": event_id, "stage": suffix, "error": "no shader"})
                continue

            entry = controller.GetShaderEntryPoints(shader_id)[0]
            reflection = controller.GetShader(rd.ResourceId(), shader_id, entry)
            raw = bytes(bytearray(reflection.rawBytes))
            raw_path = output_dir / ("EID%d-%s.dxbc" % (event_id, suffix))
            raw_path.write_bytes(raw)

            item = {
                "eventId": event_id,
                "shaderResourceId": int(shader_id),
                "entryPoint": entry.name,
                "stage": suffix,
                "rawBytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "rawPath": str(raw_path),
            }
            manifest.append(item)
finally:
    controller.Shutdown()
    cap.Shutdown()

(output_dir / "shader-raw-manifest.json").write_text(
    json.dumps(manifest, indent=2), encoding="utf-8"
)
