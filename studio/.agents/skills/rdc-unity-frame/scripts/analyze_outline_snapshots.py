"""Count RT0 changes between adjacent body/outline draw snapshots."""

import json
from pathlib import Path

import numpy as np
from PIL import Image

root = Path("E:/KianaCaptures/ZenlessZoneZero/绝区零-1790334599799/analysis-frame38112/gbuffer5-outline-snapshots")
ids = [1035, 1057, 1078, 1091, 1107, 1118, 1130, 1143, 1161, 1183]
previous = None
report = []
for eid in ids:
    current = np.asarray(Image.open(root / f"EID{eid}-RID53242.png").convert("RGB"), dtype=np.int16)
    if previous is not None:
        mask = np.max(np.abs(current - previous), axis=2) > 8
        ys, xs = np.where(mask)
        report.append({"eid": eid, "changedPixels": int(mask.sum()),
                       "boundingRect": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
                       if len(xs) else None})
    previous = current
print(json.dumps(report, ensure_ascii=False, indent=2))
