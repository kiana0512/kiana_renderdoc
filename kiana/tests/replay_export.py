"""Run using kiana_qrenderdoc.exe --python this_file (separate test process)."""
import importlib.util
import json
import os
import sys
import traceback
import renderdoc as rd

repo = os.path.abspath(os.environ.get("KIANA_TEST_ROOT", os.getcwd()))
report = os.path.join(repo,"build-early-exports","kiana-export-real.json")
cap = controller = None
try:
    spec = importlib.util.spec_from_file_location("fbx",os.path.join(repo,"kiana/extensions/kiana_bridge/fbx_export.py"))
    exporter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exporter)
    cap = rd.OpenCaptureFile()
    result = cap.OpenFile(os.path.join(repo,"dist/RenderTest-1.47-EarlyHooks-v8-x64/test-results/wuthering-v8_frame3070.rdc"),"rdc",None)
    assert result.OK(), result.Message()
    result, controller = cap.OpenCapture(rd.ReplayOptions(),None)
    assert result.OK(), result.Message()
    def flatten(actions):
        for a in actions:
            yield a
            for child in flatten(a.children):
                yield child
    samples = []
    candidates = [a for a in flatten(controller.GetRootActions()) if
                  a.flags & rd.ActionFlags.Drawcall and a.numIndices > 1000 and a.numInstances == 1]
    selected = 6093
    for a in candidates[:150]:
        controller.SetFrameEvent(a.eventId,True)
        ps = controller.GetPipelineState()
        inputs = ps.GetVertexInputs()
        info = {"event":a.eventId,"indices":a.numIndices,"buffers":len(ps.GetVBuffers()),
                "inputs":[{"name":v.name,"used":v.used,"buffer":v.vertexBuffer,"format":v.format.Name()} for v in inputs]}
        samples.append(info)
        if (ps.GetPrimitiveTopology() == rd.Topology.TriangleList and len(ps.GetVBuffers()) >= 4
            and any(v.name == "ATTRIBUTE0" and v.format.compCount == 3 for v in inputs)):
            selected = a.eventId
            break
    with open(os.path.join(repo,"build-early-exports/kiana-mesh-samples.json"),"w") as f:
        json.dump(samples,f,indent=2)
    mapping = {"position":"ATTRIBUTE0","normal":"ATTRIBUTE2","tangent":"ATTRIBUTE1","color":"ATTRIBUTE3",
               "uv0":"ATTRIBUTE4:xy","uv1":"ATTRIBUTE4:zw","uv2":"ATTRIBUTE5:xy"}
    data = exporter.export_draw(controller,selected,os.path.join(repo,"build-early-exports/kiana-exports"),True,"",mapping)
except Exception:
    data = {"error":traceback.format_exc()}
finally:
    if controller:
        controller.Shutdown()
    if cap:
        cap.Shutdown()
with open(report,"w",encoding="utf-8") as f:
    json.dump(data,f,indent=2)
sys.exit(0)
