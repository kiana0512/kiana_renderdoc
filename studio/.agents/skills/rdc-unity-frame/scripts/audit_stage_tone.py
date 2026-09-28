"""Quantify per-draw RGB/luminance differences at identical RDC/Unity stages."""

import json
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path("E:/KianaCaptures/ZenlessZoneZero/绝区零-1790334599799/analysis-frame38112")
UNITY = Path("F:/KianaFrame38112Unity/Assets/Kiana/Validation/StageRenders")
STAGES = [858, 875, 895, 912, 928, 945, 968, 992, 1008, 1035, 1057, 1078,
          1091, 1107, 1118, 1130, 1143, 1161, 1183, 1202, 1236, 1252,
          1273, 1287, 1313, 1331]
WEIGHTS = np.array([0.2126, 0.7152, 0.0722])


def source(eid):
    for folder in ["gbuffer5-outline-snapshots", "gbuffer5-snapshots", "gbuffer5-early-snapshots"]:
        path = ROOT / folder / f"EID{eid}-RID53242.png"
        if path.exists():
            return np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)
    raise FileNotFoundError(eid)


def main():
    rows = []
    prev = np.zeros_like(source(STAGES[0]))
    for eid in STAGES:
        src = source(eid)
        image = UNITY / f"EID{eid}-through.png"
        if not image.exists():
            continue
        dst = np.asarray(Image.open(image).convert("RGB"), dtype=np.int16)
        if src.shape != dst.shape:
            raise ValueError((eid, src.shape, dst.shape))
        changed = np.max(np.abs(src - prev), axis=2) > 2
        foreground = np.max(src, axis=2) > 8
        mask = changed & foreground
        if not np.any(mask):
            prev = src
            continue
        delta = dst[mask] - src[mask]
        src_y = src[mask] @ WEIGHTS
        dst_y = dst[mask] @ WEIGHTS
        rows.append({
            "eid": eid, "pixels": int(mask.sum()),
            "sourceMeanY": round(float(src_y.mean()), 3),
            "unityMeanY": round(float(dst_y.mean()), 3),
            "meanYDeltaUnityMinusSource": round(float((dst_y - src_y).mean()), 3),
            "medianYDeltaUnityMinusSource": round(float(np.median(dst_y - src_y)), 3),
            "meanRGBDeltaUnityMinusSource": np.round(delta.mean(axis=0), 3).tolist(),
            "rgbMAE": round(float(np.abs(delta).mean()), 3),
        })
        prev = src
    out = Path("F:/KianaStudioElectron/docs/frame38112-stage-tone-audit.json")
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    for row in rows:
        print(f"{row['eid']:4} n={row['pixels']:7} srcY={row['sourceMeanY']:6.1f} "
              f"unityY={row['unityMeanY']:6.1f} dY={row['meanYDeltaUnityMinusSource']:+6.1f} "
              f"rgbDelta={row['meanRGBDeltaUnityMinusSource']} MAE={row['rgbMAE']:5.1f}")


if __name__ == "__main__":
    main()
