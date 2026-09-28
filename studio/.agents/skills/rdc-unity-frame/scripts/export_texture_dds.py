"""Export exact captured D3D texture resources, including their mip chains."""
import json
import os
import sys
from pathlib import Path
_candidates = [
    Path(os.environ.get('LOCALAPPDATA', '')) / 'Kiana RenderDoc' / 'pymodules',
    Path(__file__).resolve().parents[4] / 'release-next/win-unpacked/resources/kiana-runtime/pymodules',
]
_pymodules = next((path for path in _candidates if (path / 'renderdoc.pyd').is_file()), _candidates[0])
sys.path.insert(0, str(_pymodules))
import renderdoc as rd

config_path = sys.argv[1] if len(sys.argv) > 1 else os.environ['KIANA_TEXTURE_DDS_CONFIG']
config = json.loads(Path(config_path).read_text(encoding='utf-8'))
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
    controller.SetFrameEvent(int(config['event_id']), True)
    for rid in config['resource_ids']:
        destination = output / f'RID{rid}.dds'
        save = rd.TextureSave()
        save.resourceId = resources[int(rid)]
        save.destType = rd.FileType.DDS
        # The default -1 exports the original mip chain, unlike PNG mip 0.
        save.mip = -1
        result = controller.SaveTexture(save, str(destination))
        if result.code != rd.ResultCode.Succeeded:
            raise RuntimeError(f'RID{rid}: {result}')
        report.append({'resourceId': rid, 'path': str(destination),
                       'bytes': destination.stat().st_size})
finally:
    controller.Shutdown()
    capture.Shutdown()
(output / 'textures.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
