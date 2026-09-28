"""Score RDC post-VS XY against the constant-width Unity outline, per draw."""

import json
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(r"E:/KianaCaptures/ZenlessZoneZero/绝区零-1790334599799/analysis-frame38112/gbuffer5-outline-snapshots")
UNITY = Path(r"F:/KianaFrame38112Unity/Assets/Kiana/Validation/StageRenders")
DOCS = Path(r"F:/KianaStudioElectron/docs")
PREVIOUS = {1057: 1035, 1078: 1057, 1091: 1078, 1107: 1091,
            1118: 1107, 1143: 1130, 1183: 1161, 1331: 1313}


def load(path):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)


def main():
    result = []
    for eid, previous in PREVIOUS.items():
        before = load(ROOT / f"EID{previous}-RID53242.png")
        source = load(ROOT / f"EID{eid}-RID53242.png")
        baseline = load(DOCS / f"eid{eid}-baseline-outline-xy.png")
        candidate = load(DOCS / (f"eid1183-xyblend-5.png" if eid == 1183
                                 else f"eid{eid}-exact-outline-xy.png"))
        mask = np.max(np.abs(source - before), axis=2) > 1
        row = {"eid": eid, "sourceChangedPixels": int(mask.sum()),
               "baselineChangedMAE": round(float(np.abs(baseline - source)[mask].mean()), 3) if mask.any() else None,
               "exactXYChangedMAE": round(float(np.abs(candidate - source)[mask].mean()), 3) if mask.any() else None,
               "baselineFrameMAE": round(float(np.abs(baseline - source).mean()), 4),
               "exactXYFrameMAE": round(float(np.abs(candidate - source).mean()), 4)}
        result.append(row)
    output = DOCS / "frame38112-exact-outline-xy-audit.json"
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
