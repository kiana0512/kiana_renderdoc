"""Choose high-error pixels from each EID 945 material-mask band."""

import json
from pathlib import Path

import numpy as np
from PIL import Image


source = np.asarray(Image.open(Path("E:/KianaCaptures/ZenlessZoneZero/绝区零-1790334599799/analysis-frame38112/gbuffer5-snapshots/EID945-RID53242.png")).convert("RGB"), dtype=np.int16)
previous = np.asarray(Image.open(Path("E:/KianaCaptures/ZenlessZoneZero/绝区零-1790334599799/analysis-frame38112/gbuffer5-early-snapshots/EID928-RID53242.png")).convert("RGB"), dtype=np.int16)
unity = np.asarray(Image.open(Path("F:/KianaFrame38112Unity/Assets/Kiana/Validation/StageRenders/EID945-through.png")).convert("RGB"), dtype=np.int16)
mask = np.asarray(Image.open(Path("F:/KianaFrame38112Unity/Assets/Kiana/Validation/StageRenders/EID945-mask-debug.png")).convert("RGB"), dtype=np.int16)
changed_by_draw = np.abs(source - previous).max(axis=2) > 12
visible = changed_by_draw & (source.max(axis=2) > 8) & (unity.max(axis=2) > 8)
band = np.maximum(4 - np.floor(mask[:, :, 0] / 255 * 5).astype(np.int16), 0)
error = np.abs(source - unity).mean(axis=2)
chosen = []
for index in (0, 1, 2, 3, 4):
    tiles = []
    for y in range(0, source.shape[0], 120):
        for x in range(0, source.shape[1], 120):
            select = visible[y:y + 120, x:x + 120] & (band[y:y + 120, x:x + 120] == index)
            if select.sum() < 100:
                continue
            local = np.where(select, error[y:y + 120, x:x + 120], -1)
            yy, xx = np.unravel_index(np.argmax(local), local.shape)
            tiles.append((float(local[yy, xx]), x + int(xx), y + int(yy)))
    tiles.sort(reverse=True)
    for item in tiles[:6]:
        chosen.append({"band": index, "error": item[0], "x": item[1], "y": item[2]})
Path("docs/frame38112-pixel-trace-candidates.json").write_text(json.dumps(chosen, indent=2), encoding="utf-8")
print(json.dumps(chosen, indent=2))
