"""Export every source mip through RenderDoc's color-managed PNG path."""
import json
import os
from pathlib import Path
import renderdoc as rd

config = json.loads(Path(os.environ['KIANA_TEXTURE_MIPS_CONFIG']).read_text(encoding='utf-8'))
output = Path(config['output_dir'])
output.mkdir(parents=True, exist_ok=True)
capture = rd.OpenCaptureFile()
status = capture.OpenFile(config['capture'], 'rdc', None)
if not status.OK():
    raise RuntimeError(status.Message())
status, controller = capture.OpenCapture(rd.ReplayOptions(), None)
if not status.OK():
    raise RuntimeError(status.Message())
report = []
try:
    resources = {int(r.resourceId): r.resourceId for r in controller.GetResources()}
    textures = {int(t.resourceId): t for t in controller.GetTextures()}
    controller.SetFrameEvent(int(config['event_id']), True)
    for rid in config['resource_ids']:
        desc = textures[int(rid)]
        levels = []
        for mip in range(int(desc.mips)):
            destination = output / f'RID{rid}-mip{mip:02d}.png'
            save = rd.TextureSave()
            save.resourceId = resources[int(rid)]
            save.destType = rd.FileType.PNG
            save.mip = mip
            result = controller.SaveTexture(save, str(destination))
            if result.code != rd.ResultCode.Succeeded:
                raise RuntimeError(f'RID{rid} mip{mip}: {result}')
            levels.append({'mip': mip, 'path': str(destination),
                           'bytes': destination.stat().st_size})
        report.append({'resourceId': rid, 'width': desc.width,
                       'height': desc.height, 'mips': levels})
finally:
    controller.Shutdown()
    capture.Shutdown()
(output / 'mips.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
