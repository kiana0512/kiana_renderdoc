import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] /
    'release-next/win-unpacked/resources/kiana-runtime/pymodules'))
import renderdoc as rd

cfg = json.load(open(sys.argv[1], encoding='utf-8'))
capture = rd.OpenCaptureFile()
status = capture.OpenFile(cfg['capture'], 'rdc', None)
if not status.OK(): raise RuntimeError(status.Message())
status, controller = capture.OpenCapture(rd.ReplayOptions(), None)
if not status.OK(): raise RuntimeError(status.Message())
rows = []
def walk(actions):
    for a in actions:
        if cfg['first'] <= a.eventId <= cfg['last'] and a.numIndices:
            rows.append({'eventId': a.eventId, 'name': a.customName,
                         'indices': a.numIndices, 'instances': a.numInstances})
        walk(a.children)
walk(controller.GetRootActions())
Path(cfg['output']).write_text(json.dumps(rows, indent=2), encoding='utf-8')
controller.Shutdown()
capture.Shutdown()
