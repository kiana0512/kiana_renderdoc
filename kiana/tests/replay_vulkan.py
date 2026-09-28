"""Replay the linked Vulkan GPU fixtures and verify their distinct buffer data."""
import glob
import json
import os
import struct
import sys
import traceback
import renderdoc as rd

root = os.environ.get("KIANA_TEST_ROOT",os.getcwd())
directory = os.path.join(root,"build-early-exports/vulkan-linked")
report = {}
try:
    for mode, expected in (("on",{0x12340000,0x12340001}),("off",{0x12340000}),("destroy",{0x12340000})):
        values = set()
        files = []
        for filename in glob.glob(os.path.join(directory,"linked-"+mode+"_capture*.rdc")):
            cap = rd.OpenCaptureFile()
            controller = None
            try:
                result = cap.OpenFile(filename,"rdc",None)
                assert result.OK(),result.Message()
                result,controller = cap.OpenCapture(rd.ReplayOptions(),None)
                assert result.OK(),result.Message()
                actions = controller.GetRootActions()
                assert actions
                def walk(items):
                    for a in items:
                        yield a.eventId
                        for eid in walk(a.children):
                            yield eid
                controller.SetFrameEvent(max(walk(actions)),True)
                found = []
                for buffer in controller.GetBuffers():
                    if buffer.length == 256:
                        raw = controller.GetBufferData(buffer.resourceId,0,4)
                        value = struct.unpack("<I",raw)[0]
                        found.append(value)
                        values.add(value)
                files.append({"file":filename,"buffer_values":found})
            finally:
                if controller:
                    controller.Shutdown()
                cap.Shutdown()
        assert values == expected,(mode,values,expected)
        assert len(files) == len(expected),(mode,files)
        report[mode] = files
    report["passed"] = True
except Exception:
    report["error"] = traceback.format_exc()
with open(os.path.join(directory,"replay-results.json"),"w") as f:
    json.dump(report,f,indent=2)
sys.exit(0)
