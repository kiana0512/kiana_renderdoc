"""Compare frame 38112 eye/hair RT0 stages in source and Unity pixel space."""

import json
from pathlib import Path

import numpy as np
from PIL import Image


SOURCE = Path(r"E:/KianaCaptures/ZenlessZoneZero/绝区零-1790334599799/analysis-frame38112/gbuffer5-snapshots")
UNITY = Path(r"F:/KianaFrame38112Unity/Assets/Kiana/Validation/StageRenders")
OUTPUT = Path(r"F:/KianaStudioElectron/docs/frame38112-eye-hair-stage-audit.json")
STAGES = (992, 1008, 1035, 1313, 1331)
ROI = (1020, 850, 1260, 1000)  # left, top, right, bottom
PIXELS = ((1150, 920), (1150, 900), (1170, 920), (1135, 923), (1050, 1100))


def load(path):
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)


def main():
    arrays = {}
    for eid in STAGES:
        arrays[eid] = (
            load(SOURCE / f"EID{eid}-RID53242.png"),
            load(UNITY / f"EID{eid}-through.png"),
        )
    x0, y0, x1, y1 = ROI
    result = {"roi": ROI, "stages": []}
    previous = None
    for eid in STAGES:
        src, uni = arrays[eid]
        s, u = src[y0:y1, x0:x1], uni[y0:y1, x0:x1]
        entry = {
            "eid": eid,
            "roiMae": float(np.abs(s - u).mean()),
            "pixels": [
                {"xy": (x, y), "source": src[y, x].tolist(), "unity": uni[y, x].tolist()}
                for x, y in PIXELS
            ],
        }
        if previous is not None:
            prev_src, prev_uni = arrays[previous]
            source_delta = np.max(np.abs(s - prev_src[y0:y1, x0:x1]), axis=2)
            unity_delta = np.max(np.abs(u - prev_uni[y0:y1, x0:x1]), axis=2)
            mask = source_delta > 2
            entry["sourceChangedPixels"] = int(mask.sum())
            entry["unityChangedPixels"] = int((unity_delta > 2).sum())
            entry["sourceChangeMae"] = float(np.abs(s[mask] - u[mask]).mean()) if mask.any() else None
            entry["unityDrawOnlyPixels"] = int(((unity_delta > 2) & ~mask).sum())
        result["stages"].append(entry)
        previous = eid
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
